"""Download a file as served. Optional `extract: true` also unzips members into extracted/."""

from __future__ import annotations

import zipfile
from pathlib import Path

import requests

from pndata.config import USER_AGENT


def fetch(cfg: dict, workdir: Path) -> dict:
    url = cfg["url"]
    with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=300) as r:
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "text/html" in ctype and not cfg.get("allow_html"):
            raise RuntimeError(f"{url} returned HTML (soft 404?), content-type {ctype}")
        name = cfg.get("filename") or Path(r.url.split("?")[0]).name or "download"
        target = workdir / name
        with open(target, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        meta = {
            "method": "http_file",
            "request": {"url": url},
            "final_url": r.url, "http_status": r.status_code, "content_type": ctype,
            "upstream": {"etag": r.headers.get("etag"), "last_modified": r.headers.get("last-modified")},
        }
    if cfg.get("extract"):
        with zipfile.ZipFile(target) as z:
            z.extractall(workdir / "extracted")
    return meta
