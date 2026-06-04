"""One-time data preparation for the crash-cost web app.

Reads the source crash CSV + Census shapefiles from the parent `crash_costs/`
project and writes lean, map-ready artifacts under `crash_cost_app/data_cache/`:

  - crashes.parquet                          (slim crash point dataset)
  - geo/county.geojson, place.geojson, tract.geojson
                                             (Maryland-only, simplified)
  - meta.json                                (years, months, severities present)

Run from the `backend/` directory:

    python prepare_data.py

All paths are resolved relative to this file so cwd does not matter.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

HERE = Path(__file__).resolve().parent
APP_ROOT = HERE.parent
PROJECT_ROOT = APP_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE = APP_ROOT / "data_cache"
GEO_CACHE = CACHE / "geo"

CRASH_CSV = DATA_DIR / "crash_cost_eval.csv"
SHAPES = DATA_DIR / "census" / "tl2024_shapes_cache"
GEO_SUMMARY_DIR = DATA_DIR / "geo_summaries"

MD_STATEFP = "24"

COST_COMPONENTS = [
    "Medical",
    "EMS",
    "MarketProd",
    "HouseholdProd",
    "InsuranceAdmin",
    "WorkplaceCosts",
    "LegalCosts",
    "Congestion",
    "PropDamage",
    "Total_Economic",
    "QALYs",
    "TotalComp",
]

SEVERITY_LABELS = {1: "fatal", 2: "injury", 3: "property_damage"}


def _cost_col(name: str) -> str:
    return f"estimated_{name}_comp_cost_2025usd"


def gisjoin_to_geoid(gisjoin: str, level: str) -> str | None:
    """NHGIS GISJOIN → TIGER GEOID (state=24 scoped, but level-agnostic)."""
    if not isinstance(gisjoin, str) or not gisjoin.startswith("G"):
        return None
    if level == "county":
        # G + STATE(2) + '0' + COUNTY(3) + '0'
        return gisjoin[1:3] + gisjoin[4:7]
    if level == "tract":
        # G + STATE(2) + '0' + COUNTY(3) + '0' + TRACT(6)
        return gisjoin[1:3] + gisjoin[4:7] + gisjoin[8:]
    if level == "place":
        # G + STATE(2) + '0' + PLACE(5)
        return gisjoin[1:3] + gisjoin[4:]
    raise ValueError(level)


def _clean_acs_numeric(s: pd.Series) -> pd.Series:
    """NHGIS uses large negative sentinels for suppressed / missing cells."""
    v = pd.to_numeric(s, errors="coerce")
    return v.where(v >= 0, other=pd.NA)


def load_geo_enrichment(level: str) -> dict[str, dict[str, float | None]]:
    """Per GEOID: population, census vehicles-per-person, % households with no vehicle."""
    path = GEO_SUMMARY_DIR / f"merged_{level}.csv"
    if not path.exists():
        print(f"  [geo] missing {path.name}, skipping level={level}")
        return {}
    header = pd.read_csv(path, nrows=0).columns.tolist()
    base_cols = ["GISJOIN", "AUO6E001"]
    optional = ["census_est_vehicles_per_person_mid", "census_pct_hh_0_vehicles"]
    usecols = base_cols + [c for c in optional if c in header]
    df = pd.read_csv(path, usecols=usecols, dtype={"GISJOIN": str}, low_memory=False)
    df["GEOID"] = df["GISJOIN"].apply(lambda g: gisjoin_to_geoid(g, level))
    pop = _clean_acs_numeric(df["AUO6E001"])
    if "census_est_vehicles_per_person_mid" in df.columns:
        vpp = _clean_acs_numeric(df["census_est_vehicles_per_person_mid"])
    else:
        vpp = pd.Series(pd.NA, index=df.index, dtype="Float64")
    if "census_pct_hh_0_vehicles" in df.columns:
        p0 = _clean_acs_numeric(df["census_pct_hh_0_vehicles"])
    else:
        p0 = pd.Series(pd.NA, index=df.index, dtype="Float64")
    out: dict[str, dict[str, float | None]] = {}
    for geoid, p, v, z in zip(df["GEOID"], pop, vpp, p0):
        if geoid is None or (isinstance(geoid, float) and pd.isna(geoid)):
            continue
        gid = str(geoid)
        out[gid] = {
            "population": float(p) if pd.notna(p) else None,
            "vehicles_per_person": float(v) if pd.notna(v) else None,
            "pct_hh_no_vehicle": float(z) if pd.notna(z) else None,
        }
    return out


def _injury_count_columns(csv_path: Path) -> list[str]:
    hdr = pd.read_csv(csv_path, nrows=0).columns.tolist()
    occ = [c for c in hdr if c.startswith("occupants_InjuryStatus_Occ_") and c.endswith("_count")]
    nm = [c for c in hdr if c.startswith("nonmotorists_InjuryStatus_NM_") and c.endswith("_count")]
    return sorted(set(occ + nm))


def prepare_crashes() -> pd.DataFrame:
    print(f"[crashes] reading {CRASH_CSV.name} …")
    keep = [
        "Reportnumber",
        "Crash Severity",
        "Crash Severity Description",
        "crash_date",
        "CrashYear",
        "Crashhour",
        "ImpairedCrash",
        "Motorcycle Crash",
        "Non-Motorist Crash",
        "Large Vehicle Involved",
        "Latitude",
        "Longitude",
        "n_occupant_records",
        "n_nonmotorist_records",
        "n_vehicle_records",
        "GEOID_county",
        "GEOID_tract",
        "GEOID_place",
        "NAME_county",
        "NAMELSAD_tract",
        "NAMELSAD_place",
    ] + [_cost_col(c) for c in COST_COMPONENTS]
    keep = list(dict.fromkeys(keep + _injury_count_columns(CRASH_CSV)))
    keep_set = set(keep)

    df = pd.read_csv(
        CRASH_CSV,
        usecols=lambda c: c in keep_set,
        dtype={
            "GEOID_county": str,
            "GEOID_tract": str,
            "GEOID_place": str,
            "Reportnumber": str,
        },
        low_memory=False,
    )
    print(f"  {len(df):,} rows")

    df["crash_date"] = pd.to_datetime(df["crash_date"], errors="coerce")
    df["crash_year"] = df["crash_date"].dt.year.astype("Int16")
    df["crash_month"] = df["crash_date"].dt.month.astype("Int8")

    sev = pd.to_numeric(df["Crash Severity"], errors="coerce").astype("Int8")
    df["severity_code"] = sev
    df["crash_type"] = sev.map(SEVERITY_LABELS).astype("string")

    df = df.dropna(subset=["Latitude", "Longitude"]).copy()
    df["lat"] = df["Latitude"].astype("float32")
    df["lon"] = df["Longitude"].astype("float32")

    df["cost_total"] = df[_cost_col("TotalComp")].astype("float32")
    for comp in COST_COMPONENTS:
        df[f"cost_{comp.lower()}"] = df[_cost_col(comp)].astype("float32")

    for flag in ("ImpairedCrash", "Motorcycle Crash", "Non-Motorist Crash", "Large Vehicle Involved"):
        df[flag] = df[flag].map({"Yes": True, "No": False}).astype("boolean")

    def _col_sum(frame: pd.DataFrame, names: list[str]) -> pd.Series:
        present = [c for c in names if c in frame.columns]
        if not present:
            return pd.Series(0.0, index=frame.index, dtype="float64")
        return sum(frame[c].fillna(0).astype("float64") for c in present)

    occ_fatal = "occupants_InjuryStatus_Occ_1_count"
    nm_fatal = "nonmotorists_InjuryStatus_NM_1_count"
    fatal_parts: list[pd.Series] = []
    if occ_fatal in df.columns:
        fatal_parts.append(df[occ_fatal].fillna(0).astype("float64"))
    if nm_fatal in df.columns:
        fatal_parts.append(df[nm_fatal].fillna(0).astype("float64"))
    df["n_fatalities_person"] = sum(fatal_parts) if fatal_parts else pd.Series(0.0, index=df.index, dtype="float64")

    inj_codes = ("2", "3", "4", "5")
    occ_inj = [f"occupants_InjuryStatus_Occ_{c}_count" for c in inj_codes]
    nm_inj = [f"nonmotorists_InjuryStatus_NM_{c}_count" for c in inj_codes]
    df["n_injuries_person"] = _col_sum(df, occ_inj) + _col_sum(df, nm_inj)

    out = df[
        [
            "Reportnumber",
            "crash_date",
            "crash_year",
            "crash_month",
            "Crashhour",
            "severity_code",
            "crash_type",
            "lat",
            "lon",
            "n_occupant_records",
            "n_nonmotorist_records",
            "n_vehicle_records",
            "n_fatalities_person",
            "n_injuries_person",
            "ImpairedCrash",
            "Motorcycle Crash",
            "Non-Motorist Crash",
            "Large Vehicle Involved",
            "GEOID_county",
            "GEOID_tract",
            "GEOID_place",
            "NAME_county",
            "NAMELSAD_tract",
            "NAMELSAD_place",
            "cost_total",
        ]
        + [f"cost_{c.lower()}" for c in COST_COMPONENTS]
    ].rename(
        columns={
            "Reportnumber": "report_number",
            "Crashhour": "crash_hour",
            "ImpairedCrash": "impaired",
            "Motorcycle Crash": "motorcycle",
            "Non-Motorist Crash": "nonmotorist",
            "Large Vehicle Involved": "large_vehicle",
            "NAME_county": "county_name",
            "NAMELSAD_tract": "tract_name",
            "NAMELSAD_place": "place_name",
        }
    )

    out_path = CACHE / "crashes.parquet"
    out.to_parquet(out_path, compression="zstd", index=False)
    print(f"  -> {out_path.relative_to(APP_ROOT)} ({out_path.stat().st_size / 1e6:.1f} MB)")
    return out


def prepare_geojson(
    level: str,
    shapefile_dir: Path,
    shapefile_name: str,
    simplify_tol: float,
    geo_attrs: dict[str, dict[str, float | None]],
) -> None:
    shp = shapefile_dir / shapefile_name
    if not shp.exists():
        print(f"[geo:{level}] missing {shp}, skipping")
        return

    print(f"[geo:{level}] reading {shp.name} …")
    try:
        gdf = gpd.read_file(shp, where=f"STATEFP = '{MD_STATEFP}'")
    except (ValueError, TypeError):
        # Fallback when the active engine doesn't accept `where`.
        gdf = gpd.read_file(shp)
        gdf = gdf[gdf["STATEFP"] == MD_STATEFP].copy()
    print(f"  {len(gdf)} MD features")

    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf["geometry"].simplify(simplify_tol, preserve_topology=True)

    if level == "county":
        gdf["name"] = gdf["NAMELSAD"]
        keep_attrs = ["GEOID", "name"]
    elif level == "tract":
        gdf["name"] = gdf["NAMELSAD"]
        keep_attrs = ["GEOID", "name", "COUNTYFP"]
    elif level == "place":
        gdf["name"] = gdf["NAMELSAD"]
        gdf["lsad"] = gdf["LSAD"] if "LSAD" in gdf.columns else None
        keep_attrs = ["GEOID", "name", "lsad"]
    else:
        raise ValueError(level)

    def _pick(geoid: str, key: str) -> float | None:
        row = geo_attrs.get(geoid) or {}
        v = row.get(key)
        return v if isinstance(v, (int, float)) or v is None else None

    gdf["population"] = gdf["GEOID"].map(lambda gid: _pick(str(gid), "population")).astype("Float64")
    gdf["vehicles_per_person"] = gdf["GEOID"].map(lambda gid: _pick(str(gid), "vehicles_per_person")).astype("Float64")
    gdf["pct_hh_no_vehicle"] = gdf["GEOID"].map(lambda gid: _pick(str(gid), "pct_hh_no_vehicle")).astype("Float64")
    props = keep_attrs + ["population", "vehicles_per_person", "pct_hh_no_vehicle"]
    gdf = gdf[props + ["geometry"]]

    out_path = GEO_CACHE / f"{level}.geojson"
    # Write with default precision, then post-process to 5-decimal lat/lon
    # (~1 m) — shrinks files ~2-3× without depending on engine-specific
    # `COORDINATE_PRECISION` support.
    if out_path.exists():
        out_path.unlink()
    gdf.to_file(out_path, driver="GeoJSON")
    import re

    text = out_path.read_text()
    text = re.sub(r"(-?\d+\.\d{5})\d+", r"\1", text)
    out_path.write_text(text)
    print(f"  -> {out_path.relative_to(APP_ROOT)} ({out_path.stat().st_size / 1e6:.2f} MB)")


def write_meta(crashes: pd.DataFrame) -> None:
    years = sorted(int(y) for y in crashes["crash_year"].dropna().unique())
    months = sorted(int(m) for m in crashes["crash_month"].dropna().unique())
    crash_types = sorted(t for t in crashes["crash_type"].dropna().unique().tolist())
    dmin = crashes["crash_date"].min()
    dmax = crashes["crash_date"].max()
    meta = {
        "years": years,
        "months": months,
        "crash_types": crash_types,
        "n_crashes": int(len(crashes)),
        "cost_components": COST_COMPONENTS,
        "min_crash_date": pd.Timestamp(dmin).date().isoformat() if pd.notna(dmin) else None,
        "max_crash_date": pd.Timestamp(dmax).date().isoformat() if pd.notna(dmax) else None,
    }
    (CACHE / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[meta] {meta['n_crashes']:,} crashes, years={years}, crash_types={crash_types}")


def main() -> None:
    CACHE.mkdir(exist_ok=True)
    GEO_CACHE.mkdir(exist_ok=True)

    crashes = prepare_crashes()

    for level, tol, shp_dir, shp_name in (
        ("county", 0.0005, SHAPES / "county", "US_county_2024.shp"),
        ("place", 0.0003, SHAPES / "place", "US_place_2024.shp"),
        ("tract", 0.0002, SHAPES / "tract", "US_tract_2024.shp"),
    ):
        prepare_geojson(level, shp_dir, shp_name, tol, load_geo_enrichment(level))

    write_meta(crashes)
    print("done.")


if __name__ == "__main__":
    main()
