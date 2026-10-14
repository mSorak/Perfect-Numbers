"""Census Data API: one JSON file per table group × geography, as served, plus each group's variable labels."""

from __future__ import annotations

import json
from pathlib import Path

import requests

from pndata.config import USER_AGENT, get_key

BASE = "https://api.census.gov/data"


def _get(url: str, params: dict | None = None) -> list | dict:
    r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=180)
    if "<title>Invalid Key</title>" in r.text:
        raise RuntimeError("Census API says CENSUS_API_KEY is invalid. New keys must be activated from the "
                           "emailed link; otherwise request a new key at https://api.census.gov/data/key_signup.html")
    if r.status_code != 200 or not r.text.lstrip().startswith(("[", "{")):
        # error bodies are HTML/text; never echo the URL (it carries the key)
        raise RuntimeError(f"Census API {r.status_code} for {url}: {r.text[:200]}")
    return r.json()


def fetch(cfg: dict, workdir: Path) -> dict:
    """cfg: {dataset: acs/acs5, vintage: 2024, groups: [B01003], geographies: {county: {for: 'county:*', in: 'state:24'}}}"""
    url = f"{BASE}/{cfg['vintage']}/{cfg['dataset']}"
    key = get_key("CENSUS_API_KEY")
    rows, requests_made = 0, []
    for group in cfg["groups"]:
        labels = _get(f"{url}/groups/{group}.json")  # no key needed
        (workdir / f"{group}_variables.json").write_text(json.dumps(labels, indent=1), encoding="utf-8")
        for geo_name, geo in cfg["geographies"].items():
            params = {"get": f"NAME,group({group})", "for": geo["for"], **({"in": geo["in"]} if geo.get("in") else {})}
            data = _get(url, {**params, "key": key})
            (workdir / f"{group}_{geo_name}.json").write_text(json.dumps(data), encoding="utf-8")
            rows += len(data) - 1
            requests_made.append(params)
    return {"method": "census_api", "request": {"url": url, "params": {"calls": requests_made, "key": "<redacted>"}},
            "rows": rows, "vintage": {"dataset": cfg["dataset"], "vintage": cfg["vintage"],
                                      "label": cfg.get("label")}}
