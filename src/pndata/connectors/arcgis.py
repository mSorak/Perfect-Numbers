"""ArcGIS FeatureServer/MapServer layer → one GeoJSON file (paged), plus the layer's metadata."""

from __future__ import annotations

import json
from pathlib import Path

import requests

from pndata.config import USER_AGENT


def _get(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=180)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"{url}: {j['error']}")
    return j


def fetch(cfg: dict, workdir: Path) -> dict:
    layer_url = cfg["url"].rstrip("/")
    where = cfg.get("where", "1=1")
    layer = _get(layer_url, {"f": "json"})
    (workdir / "_layer.json").write_text(json.dumps(layer, indent=1), encoding="utf-8")
    oid = layer.get("objectIdField") or "OBJECTID"
    page = min(int(cfg.get("page_size", 2000)), int(layer.get("maxRecordCount") or 2000))
    total = _get(f"{layer_url}/query", {"where": where, "returnCountOnly": "true", "f": "json"})["count"]

    features, offset = [], 0
    while offset < total:
        params = {"where": where, "outFields": cfg.get("out_fields", "*"), "outSR": 4326, "f": "geojson",
                  "orderByFields": oid, "resultOffset": offset, "resultRecordCount": page}
        batch = _get(f"{layer_url}/query", params).get("features", [])
        if not batch:
            break
        features += batch
        offset += len(batch)
    if len(features) != total:
        raise RuntimeError(f"{layer_url}: expected {total} features, got {len(features)}")

    out = workdir / cfg.get("filename", "features.geojson")
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")
    edit = (layer.get("editingInfo") or {}).get("dataLastEditDate")
    return {
        "method": "arcgis",
        "request": {"url": f"{layer_url}/query", "params": {"where": where, "outSR": 4326, "f": "geojson"}},
        "rows": len(features),
        "upstream": {"dataLastEditDate": edit, "name": layer.get("name")},
    }
