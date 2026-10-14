"""Socrata (SODA 2.1) dataset → CSV pages concatenated into one file."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import requests

from pndata.config import USER_AGENT, get_key


def fetch(cfg: dict, workdir: Path) -> dict:
    base = f"https://{cfg['domain']}/resource/{cfg['dataset']}.csv"
    headers = {"User-Agent": USER_AGENT}
    token = get_key("SOCRATA_APP_TOKEN", required=False)
    if token:
        headers["X-App-Token"] = token
    page = int(cfg.get("page_size", 50000))
    params = {"$order": ":id", "$limit": page}
    if cfg.get("where"):
        params["$where"] = cfg["where"]
    if cfg.get("select"):
        params["$select"] = cfg["select"]

    out = workdir / cfg.get("filename", f"{cfg['dataset']}.csv")
    rows, offset, header = 0, 0, None
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        while True:
            r = requests.get(base, params={**params, "$offset": offset}, headers=headers, timeout=300)
            r.raise_for_status()
            reader = csv.reader(io.StringIO(r.text))
            page_header = next(reader, None)
            body = list(reader)
            if header is None and page_header:
                header = page_header
                writer.writerow(header)
            writer.writerows(body)
            rows += len(body)
            offset += page
            if len(body) < page:
                break
    return {"method": "socrata", "rows": rows,
            "request": {"url": base, "params": {k: v for k, v in params.items() if k != "$limit"}}}
