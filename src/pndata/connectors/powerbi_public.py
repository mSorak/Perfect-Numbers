"""Public ("publish to web") Power BI report → raw querydata JSON per entity.

Undocumented endpoint (fragile). The raw response is kept verbatim; decoding happens in staging
(`pndata.powerbi.decode_dsr`). Config: resource_key, cluster, model_id, view_url, entity, columns.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import requests


def _col(prop: str, alias: str = "t") -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
            "Name": f"{alias}.{prop}"}


def fetch(cfg: dict, workdir: Path) -> dict:
    cols = cfg["columns"]
    payload = {
        "version": "1.0.0",
        "queries": [{
            "Query": {"Commands": [{"SemanticQueryDataShapeCommand": {
                "Query": {"Version": 2, "From": [{"Name": "t", "Entity": cfg["entity"], "Type": 0}],
                          "Select": [_col(c) for c in cols]},
                "Binding": {"Primary": {"Groupings": [{"Projections": list(range(len(cols)))}]},
                            "DataReduction": {"DataVolume": 6,
                                              "Primary": {"Window": {"Count": int(cfg.get("window", 200000))}}},
                            "Version": 1}}}]},
            "QueryId": "",
            "ApplicationContext": {"DatasetId": "", "Sources": [{"ReportId": cfg["resource_key"]}]},
        }],
        "cancelQueries": [],
        "modelId": int(cfg["model_id"]),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://app.powerbigov.us", "Referer": cfg["view_url"],
        "X-PowerBI-ResourceKey": cfg["resource_key"], "Content-Type": "application/json;charset=UTF-8",
        "ActivityId": str(uuid.uuid4()), "RequestId": str(uuid.uuid4()),
    }
    url = cfg["cluster"].rstrip("/") + "/public/reports/querydata?synchronous=true"
    r = requests.post(url, json=payload, headers=headers, timeout=300)
    r.raise_for_status()
    body = r.json()
    if "error" in json.dumps(body)[:2000].lower() and "results" not in body:
        raise RuntimeError(f"Power BI query failed for {cfg['entity']}: {r.text[:500]}")
    (workdir / "querydata.json").write_text(r.text, encoding="utf-8")
    (workdir / "_query.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return {"method": "powerbi_public", "http_status": r.status_code,
            "request": {"url": url, "params": {"entity": cfg["entity"], "columns": cols, "model_id": cfg["model_id"]}}}
