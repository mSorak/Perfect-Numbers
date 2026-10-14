"""Decode Power BI DSR (data shape result) JSON into rows. Adapted from 2026/mta_overview/build_mta_xlsx.py."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def decode_dsr(path: Path) -> tuple[list[str], list[list]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    data = raw["results"][0]["result"]["data"]
    colnames = [s["Name"].split(".", 1)[-1] for s in data["descriptor"]["Select"]]
    ds = data["dsr"]["DS"][0]
    dicts = ds.get("ValueDicts") or {}
    schema, prev, rows = None, [None] * len(colnames), []
    for rec in ds["PH"][0]["DM0"]:
        if "S" in rec:
            schema = rec["S"]
        n = len(schema)
        C, R, nulls = rec.get("C") or [], rec.get("R") or 0, rec.get("Ø") or 0
        vals, ci = [], 0
        for i in range(n):
            bit = 1 << i
            if nulls & bit:
                vals.append(None)
            elif R & bit:
                vals.append(prev[i])
            else:
                vals.append(C[ci])
                ci += 1
        out = []
        for i, spec in enumerate(schema):
            v = vals[i]
            if v is None:
                out.append(None)
                continue
            dn, t = spec.get("DN"), spec.get("T")
            if dn and isinstance(v, int) and dn in dicts and 0 <= v < len(dicts[dn]):
                v = dicts[dn][v]
            if t == 7:
                v = datetime.fromtimestamp(int(v) / 1000, tz=timezone.utc).date()
            elif t == 3:
                v = float(v)
            elif t == 4:
                v = int(v)
            out.append(v)
        prev = vals
        rows.append(out)
    return colnames, rows
