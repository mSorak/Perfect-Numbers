"""FastAPI entry point for the crash-cost web app."""

from __future__ import annotations

from typing import Any

import orjson
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from . import data as data_module
from .config import DEV_ORIGINS, FRONTEND_DIST
from .metrics import DEFAULT_METRIC_ID, METRICS, METRICS_BY_ID, MetricDef, compute_metric_value

app = FastAPI(title="Crash Cost App", default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)


def _parse_csv_ints(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(v) for v in value.split(",") if v.strip()]


def _parse_csv_strs(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


# Default aggregate row when a geography has no crashes under the active filters.
_ZERO_AGG: dict[str, Any] = {
    "n_crashes": 0,
    "n_fatal": 0,
    "n_injury": 0,
    "n_property_damage": 0,
    "sum_cost_total": 0.0,
    "sum_cost_medical": 0.0,
    "sum_cost_ems": 0.0,
    "sum_cost_marketprod": 0.0,
    "sum_cost_householdprod": 0.0,
    "sum_cost_insuranceadmin": 0.0,
    "sum_cost_workplacecosts": 0.0,
    "sum_cost_legalcosts": 0.0,
    "sum_cost_congestion": 0.0,
    "sum_cost_propdamage": 0.0,
    "sum_cost_cong_propdamage": 0.0,
    "sum_cost_total_economic": 0.0,
    "sum_cost_qalys": 0.0,
    "sum_cost_totalcomp": 0.0,
    "sum_occupants": 0,
    "sum_nonmotorists": 0,
    "sum_vehicles": 0,
    "sum_fatalities_person": 0,
    "sum_injuries_person": 0,
}


def _summary_features_for_level(
    level: str,
    metric_def: MetricDef,
    rows: list[dict[str, Any]],
    geo_props: dict[str, dict[str, float | None]],
) -> list[dict[str, Any]]:
    """One feature per GeoJSON polygon, with zero-filled rows where filters match no crashes."""
    rows_by_geoid = {str(r["geoid"]): r for r in rows if r.get("geoid") is not None}
    gj = orjson.loads(data_module.load_geojson_raw(level))
    features: list[dict[str, Any]] = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        geoid = props.get("GEOID")
        if geoid is None:
            continue
        gid = str(geoid)
        row = rows_by_geoid.get(gid, {**_ZERO_AGG, "geoid": gid})
        extras = geo_props.get(gid) or {}
        row_merged = {**row, **extras}
        value = compute_metric_value(metric_def, row_merged)
        features.append({"geoid": gid, "value": value, **row_merged})
    return features


@app.get("/api/health")
def health() -> dict[str, Any]:
    try:
        meta = data_module.load_meta()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "n_crashes": meta.get("n_crashes"), "years": meta.get("years")}


@app.get("/api/metadata")
def metadata() -> dict[str, Any]:
    meta = data_module.load_meta()
    return {
        "years": meta.get("years", []),
        "months": meta.get("months", list(range(1, 13))),
        "crash_types": meta.get("crash_types", []),
        "cost_components": meta.get("cost_components", []),
        "min_crash_date": meta.get("min_crash_date"),
        "max_crash_date": meta.get("max_crash_date"),
        "metrics": [
            {
                "id": m.id,
                "label": m.label,
                "format": m.format,
                "denominator": m.denominator,
                "rate_per": m.rate_per,
                "description": m.description,
            }
            for m in METRICS
        ],
        "default_metric": DEFAULT_METRIC_ID,
        "levels": ["county", "place", "tract"],
    }


@app.get("/api/geo/{level}")
def geo(level: str) -> Response:
    if level not in ("county", "place", "tract"):
        raise HTTPException(404, f"unknown level: {level}")
    try:
        geojson = data_module.load_geojson_raw(level)
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc))
    return Response(
        content=geojson,
        media_type="application/geo+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/api/summary/state")
def summary_state(
    metric: str = Query(DEFAULT_METRIC_ID),
    years: str | None = Query(None),
    months: str | None = Query(None),
    crash_types: str | None = Query(None),
    date_from: str | None = Query(None, description="ISO date YYYY-MM-DD; use with date_to"),
    date_to: str | None = Query(None, description="ISO date YYYY-MM-DD"),
    nonmotorist: bool = Query(False, description="If true, only crashes with a non-motorist involved"),
) -> dict[str, Any]:
    metric_def = METRICS_BY_ID.get(metric)
    if metric_def is None:
        raise HTTPException(400, f"unknown metric: {metric}")

    year_list = _parse_csv_ints(years)
    month_list = _parse_csv_ints(months)
    type_list = _parse_csv_strs(crash_types)
    date_from_s = date_from.strip() if date_from else None
    date_to_s = date_to.strip() if date_to else None
    if (date_from_s or date_to_s) and not (date_from_s and date_to_s):
        raise HTTPException(400, "date_from and date_to must both be set, or both omitted")

    row = data_module.aggregate_state(
        year_list,
        month_list,
        type_list,
        date_from=date_from_s,
        date_to=date_to_s,
        nonmotorist_only=nonmotorist,
    )
    if row is None:
        features: list[dict[str, Any]] = []
    else:
        county_props = _load_geo_props("county")
        population = sum(
            (p.get("population") or 0)
            for p in county_props.values()
            if isinstance(p.get("population"), (int, float))
        )
        row_merged = {**row, "population": population or None, "geoid": str(row["geoid"])}
        value = compute_metric_value(metric_def, row_merged)
        features = [{"geoid": row_merged["geoid"], "value": value, **row_merged}]

    return {
        "level": "state",
        "metric": metric_def.id,
        "filters": {
            "years": year_list,
            "months": month_list,
            "crash_types": type_list,
            "date_from": date_from_s,
            "date_to": date_to_s,
            "nonmotorist": nonmotorist,
        },
        "features": features,
    }


@app.get("/api/summary/{level}")
def summary(
    level: str,
    metric: str = Query(DEFAULT_METRIC_ID),
    years: str | None = Query(None),
    months: str | None = Query(None),
    crash_types: str | None = Query(None),
    date_from: str | None = Query(None, description="ISO date YYYY-MM-DD; use with date_to"),
    date_to: str | None = Query(None, description="ISO date YYYY-MM-DD"),
    nonmotorist: bool = Query(False, description="If true, only crashes with a non-motorist involved"),
) -> dict[str, Any]:
    if level not in ("county", "place", "tract"):
        raise HTTPException(404, f"unknown level: {level}")
    metric_def = METRICS_BY_ID.get(metric)
    if metric_def is None:
        raise HTTPException(400, f"unknown metric: {metric}")

    year_list = _parse_csv_ints(years)
    month_list = _parse_csv_ints(months)
    type_list = _parse_csv_strs(crash_types)
    date_from_s = date_from.strip() if date_from else None
    date_to_s = date_to.strip() if date_to else None
    if (date_from_s or date_to_s) and not (date_from_s and date_to_s):
        raise HTTPException(400, "date_from and date_to must both be set, or both omitted")

    rows = data_module.aggregate_by_geo(
        level,
        year_list,
        month_list,
        type_list,
        date_from=date_from_s,
        date_to=date_to_s,
        nonmotorist_only=nonmotorist,
    )

    geo_props = _load_geo_props(level)
    features = _summary_features_for_level(level, metric_def, rows, geo_props)

    return {
        "level": level,
        "metric": metric_def.id,
        "filters": {
            "years": year_list,
            "months": month_list,
            "crash_types": type_list,
            "date_from": date_from_s,
            "date_to": date_to_s,
            "nonmotorist": nonmotorist,
        },
        "features": features,
    }


@app.get("/api/crashes")
def crashes(
    west: float = Query(...),
    south: float = Query(...),
    east: float = Query(...),
    north: float = Query(...),
    years: str | None = Query(None),
    months: str | None = Query(None),
    crash_types: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    nonmotorist: bool = Query(False),
    limit: int = Query(50_000, ge=1, le=250_000),
) -> dict[str, Any]:
    date_from_s = date_from.strip() if date_from else None
    date_to_s = date_to.strip() if date_to else None
    if (date_from_s or date_to_s) and not (date_from_s and date_to_s):
        raise HTTPException(400, "date_from and date_to must both be set, or both omitted")
    points = data_module.fetch_crashes_in_bbox(
        west=west,
        south=south,
        east=east,
        north=north,
        years=_parse_csv_ints(years),
        months=_parse_csv_ints(months),
        crash_types=_parse_csv_strs(crash_types),
        date_from=date_from_s,
        date_to=date_to_s,
        nonmotorist_only=nonmotorist,
        limit=limit,
    )
    return {"count": len(points), "limit": limit, "points": points}


def _load_geo_props(level: str) -> dict[str, dict[str, float | None]]:
    """Population + census vehicle fields from prepared GeoJSON properties."""
    cache_key = f"_geo_props_{level}"
    cached = getattr(_load_geo_props, cache_key, None)
    if cached is not None:
        return cached
    raw = data_module.load_geojson_raw(level)
    gj = orjson.loads(raw)
    out: dict[str, dict[str, float | None]] = {}
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        geoid = props.get("GEOID")
        if geoid is None:
            continue
        gid = str(geoid)

        def num(v: object) -> float | None:
            return v if isinstance(v, (int, float)) else None

        out[gid] = {
            "population": num(props.get("population")),
            "vehicles_per_person": num(props.get("vehicles_per_person")),
            "pct_hh_no_vehicle": num(props.get("pct_hh_no_vehicle")),
        }
    setattr(_load_geo_props, cache_key, out)
    return out


if FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIST), html=True),
        name="frontend",
    )
