"""BLS Public Data API v2: time series → one JSON file per request chunk (≤20 years each), as served."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests

from pndata.config import USER_AGENT, get_key

URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
MAX_YEARS = 20  # per request, with a registration key


def fetch(cfg: dict, workdir: Path) -> dict:
    series = cfg["series"]
    start = int(cfg["start_year"])
    end = int(cfg.get("end_year") or date.today().year)
    key = get_key("BLS_API_KEY")
    rows, chunks = 0, []
    for y0 in range(start, end + 1, MAX_YEARS):
        y1 = min(y0 + MAX_YEARS - 1, end)
        body = {"seriesid": series, "startyear": str(y0), "endyear": str(y1), "annualaverage": True}
        r = requests.post(URL, json={**body, "registrationkey": key},
                          headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        j = r.json()
        if j.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS {y0}-{y1}: {j.get('status')} {j.get('message')}")
        if j.get("message"):  # warnings such as "No data for series X in year Y"
            chunks.append({"years": [y0, y1], "messages": j["message"]})
        (workdir / f"bls_{y0}_{y1}.json").write_text(json.dumps(j["Results"], indent=1), encoding="utf-8")
        rows += sum(len(s["data"]) for s in j["Results"]["series"])
    return {"method": "bls_api", "request": {"url": URL, "params": {"seriesid": series, "startyear": start,
            "endyear": end, "annualaverage": True}}, "rows": rows,
            **({"api_messages": chunks} if chunks else {})}
