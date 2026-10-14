"""ACS 5-year tables from Census API snapshots → long format (geo × variable), estimates with MOEs.

Each raw file is `<GROUP>_<geo level>.json` as served (first row = header), plus `<GROUP>_variables.json`
(labels). Jam values (e.g. -666666666 'not available') become null and are flagged in `annotation`.
"""

import json
from pathlib import Path

import pandas as pd

ENTITIES = ["census_api/acs5_2024"]
JAM = {-111111111, -222222222, -333333333, -555555555, -666666666, -888888888, -999999999}


def long_from_snapshot(folder: Path, vintage: int, label: str, snapshot_id: str) -> pd.DataFrame:
    frames = []
    for f in sorted(folder.glob("*_*.json")):
        if f.name.startswith("_") or f.name.endswith("_variables.json"):
            continue
        group, level = f.stem.split("_", 1)
        labels = json.loads((folder / f"{group}_variables.json").read_text(encoding="utf-8"))["variables"]
        rows = json.loads(f.read_text(encoding="utf-8"))
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df = df.loc[:, ~df.columns.duplicated()]  # get=NAME,group(X) returns NAME twice
        est = [c for c in df.columns if c.startswith(group) and c.endswith("E") and c[:-1] + "M" in df.columns]
        for c in est:
            var = c[:-1]
            e = pd.to_numeric(df[c], errors="coerce")
            m = pd.to_numeric(df[var + "M"], errors="coerce")
            ann = df.get(var + "EA")
            frames.append(pd.DataFrame({
                "geoid": df["GEO_ID"].str.split("US").str[-1],
                "geo_level": level,
                "name": df["NAME"],
                "vintage": vintage,
                "survey": "acs5",
                "vintage_label": label,
                "table_id": group,
                "variable": var,
                "label": labels.get(c, {}).get("label"),
                "estimate": e.where(~e.isin(JAM)),
                "moe": m.where(~m.isin(JAM) & (m >= 0)),
                "annotation": (ann.where(ann.notna() & (ann != "null")) if ann is not None else None),
                "source_snapshot_id": snapshot_id,
            }))
    return pd.concat(frames, ignore_index=True)


def acs5(con, ctx):
    out = []
    for key in ENTITIES:
        folder = ctx.raw(key)
        rec = ctx.raw_inputs[key]
        v = rec.get("vintage", {})
        out.append(long_from_snapshot(folder, int(v.get("vintage")), v.get("label") or "", rec["snapshot_id"]))
    df = pd.concat(out, ignore_index=True)
    df["geoid_vintage"] = 2020  # ACS 2020–2024 uses 2020-census geographies
    return df
