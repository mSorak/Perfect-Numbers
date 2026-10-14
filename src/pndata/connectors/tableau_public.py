"""`tableau_public` connector: row-level export from a public Tableau Server view via a guest session.

Route found in the 2026-10-14 spike (docs/design/05_mdsp_tableau_spike.md). It makes the same calls as the
dashboard's "Download > Data > <tab> > Show all fields > Download" button, with no browser:

  1. POST /vizql/t/{site}/w/{wb}/v/{view}/startSession/viewing?<view params>  → tsConfig (sessionid)
  2. POST .../bootstrapSession/sessions/{sid}  (passes tsConfig.showParams, so URL parameters apply)
  3. tabdoc/api-get-worksheet-logical-table-ids        → logical tables (Reports, Vehicles, …) by caption
  4. tabdoc/api-get-worksheet-underlying-logical-table-data, 1-day window → full column list per table
     (this command is capped at 10,000 rows, so it is used only to learn the columns)
  5. tabdoc/set-parameter-value ×2                      → the real window (about 9 s each; dashboard re-renders)
  6. tabsrv/export-view-data-underlying-to-csv-server {viewDataTableId, columns, showAliases}
     → resultKey arrives in a doc:export-file-notification-event; GET .../tempfile/sessions/{sid}?key=…
     → the exact CSV the UI downloads (UTF-8 BOM, M/D/YYYY, aliases). No row cap observed.

All tables of one window come from one session, so a batch passes intake's same-session and orphan checks.
The vizql commands are undocumented and may change when the server is upgraded; the connector fails loudly
on any unexpected shape, and `pn intake` then checks the files. Config lives in the source card's `fetch:`
block (host, site, workbook, view, worksheet, params, url_params, tables). Don't parallelise: one session at
a time, about 35 s per month.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse as up
import uuid
from datetime import date, timedelta
from pathlib import Path

import requests

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141 Safari/537.36"


class TableauGuest:
    def __init__(self, host: str, site: str, workbook: str, view: str, url_params: dict[str, str]):
        self.host, self.site, self.wb, self.view = host.rstrip("/"), site, workbook, view
        self.http = requests.Session()
        self.http.headers["User-Agent"] = BROWSER_UA
        q = up.urlencode({":embed": "y", ":showVizHome": "no", **url_params}, quote_via=up.quote)
        self.view_url = f"{self.host}/t/{site}/views/{workbook}/{view}?{q}"
        self.http.get(self.view_url, timeout=60).raise_for_status()
        r = self.http.post(
            f"{self.host}/vizql/t/{site}/w/{workbook}/v/{view}/startSession/viewing?{q}", timeout=120,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded",
                     "Tableau-Viz-Location": self.view_url, "Tableau-Viz-Path": f"/t/{site}/w/{workbook}",
                     "X-B3-TraceID": uuid.uuid4().hex, "X-B3-SpanID": uuid.uuid4().hex[:16], "X-B3-Sampled": "1"})
        r.raise_for_status()
        self.ts = r.json()
        if not self.ts.get("allow_export_data") or not self.ts.get("allow_view_underlying"):
            raise RuntimeError("guest session does not allow data export (publisher changed permissions?)")
        self.sid = self.ts["sessionid"]
        self.root = f"{self.host}{self.ts['vizql_root']}"
        self._bootstrap()

    def _headers(self) -> dict:
        return {"Accept": "text/javascript", "X-Tsi-Active-Tab": self.view, "Origin": self.host, "Referer": self.view_url}

    def _bootstrap(self) -> None:
        port = '{"w":1600,"h":1000}'
        data = {"worksheetPortSize": port, "dashboardPortSize": port, "clientDimension": port,
                "renderMapsClientSide": "true", "isBrowserRendering": "true", "browserRenderingThreshold": "100",
                "formatDataValueLocally": "false", "clientNum": "", "navType": "Nav", "navSrc": "Boot",
                "devicePixelRatio": "1", "clientRenderPixelLimit": "16000000",
                "allowAutogenWorksheetPhoneLayouts": "false", "sheet_id": self.view,
                "showParams": self.ts["showParams"], "stickySessionKey": self.ts.get("stickySessionKey") or "",
                "filterTileSize": "200", "locale": "en_US", "language": "en", "verboseMode": "false",
                ":session_feature_flags": "{}", "keychain_version": "1"}
        r = self.http.post(f"{self.root}/bootstrapSession/sessions/{self.sid}", data=data,
                           headers=self._headers(), timeout=300)
        r.raise_for_status()

    def command(self, ns: str, name: str, params: dict) -> requests.Response:
        r = self.http.post(f"{self.root}/sessions/{self.sid}/commands/{ns}/{name}", data=params,
                           headers=self._headers(), timeout=600)
        r.raise_for_status()
        if '"errorResponseType"' in r.text[:200] or '"valid": false' in r.text[:4000]:
            raise RuntimeError(f"{ns}/{name} rejected: {r.text[:500]}")
        return r

    @staticmethod
    def result(r: requests.Response) -> dict:
        return r.json()["vqlCmdResponse"]["cmdResultList"][0]["commandReturn"]

    def set_parameter(self, name: str, d: date) -> None:
        self.command("tabdoc", "set-parameter-value",
                     {"globalFieldName": name, "valueString": f"{d.month}/{d.day}/{d.year}", "useUsLocale": "true"})

    def download(self, key: str) -> bytes:
        r = self.http.get(f"{self.root}/tempfile/sessions/{self.sid}",
                          params={"key": key, "keepfile": "yes", "attachment": "yes"},
                          headers=self._headers(), timeout=600)
        r.raise_for_status()
        return r.content


def fetch(cfg: dict, workdir: Path) -> dict:
    """Write one CSV per logical table for [cfg.start, cfg.end] into workdir, all from one guest session."""
    start, end = date.fromisoformat(cfg["start"]), date.fromisoformat(cfg["end"])
    up_names, p_names = cfg["url_params"], cfg["params"]
    vis = {"worksheet": cfg["worksheet"], "dashboard": cfg["view"]}
    base = {**vis, "visualIdPresModel": json.dumps(vis), "versionName": "1.0.0"}

    # Boot on a 1-day window: step 4 then returns small payloads.
    t0 = time.time()
    tg = TableauGuest(cfg["host"], cfg["site"], cfg["workbook"], cfg["view"],
                      {up_names["begin"]: start.isoformat(), up_names["end"]: start.isoformat()})
    found = {t["showDataTableCaption"]: t["showDataTableId"] for t in
             tg.result(tg.command("tabdoc", "api-get-worksheet-logical-table-ids", base))["showDataTableIdWithCaptionList"]}
    wanted = cfg["tables"]
    unexpected = sorted(set(found) - set(wanted.values()))
    missing = sorted(set(wanted.values()) - set(found))
    if missing:
        raise RuntimeError(f"logical tables missing upstream: {missing} (found {sorted(found)})")

    columns = {}
    for entity, caption in wanted.items():
        dt = tg.result(tg.command("tabdoc", "api-get-worksheet-underlying-logical-table-data",
                                  {**base, "showDataTableId": found[caption], "maxRows": "1",
                                   "ignoreAliases": "false", "ignoreSelection": "true",
                                   "includeAllColumns": "true"}))["dataTablePresModel"]
        columns[entity] = [c["uniqueName"] for c in dt["showDataTableColumnPresModels"]]

    tg.set_parameter(p_names["begin"], start)
    tg.set_parameter(p_names["end"], end)

    tables = {}
    for entity, caption in wanted.items():
        r = tg.command("tabsrv", "export-view-data-underlying-to-csv-server",
                       {"visualIdPresModel": json.dumps(vis), "showAliases": "true",
                        "columns": json.dumps(columns[entity]), "viewDataTableId": found[caption]})
        m = re.search(r'"genExportFilePresModel":\{"resultKey": "(\d+)"', r.text)
        if not m:
            raise RuntimeError(f"no export file for {caption}: {r.text[-300:]}")
        body = tg.download(m.group(1))
        if not body.startswith(b"\xef\xbb\xbf"):
            raise RuntimeError(f"{caption}: export is not UTF-8-with-BOM CSV (got {body[:60]!r})")
        target = workdir / f"{entity}_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        target.write_bytes(body)
        time.sleep(1)
        tables[entity] = {"caption": caption, "logical_table_id": found[caption], "file": target.name,
                          "bytes": len(body), "rows": body.count(b"\n") - 1,  # approximate; intake counts properly
                          "columns": len(columns[entity])}

    return {"method": "tableau_public",
            "request": {"boot_url": tg.view_url,  # 1-day boot window; the export window is `window`
                        "window": [start.isoformat(), end.isoformat()],
                        "commands": ["api-get-worksheet-logical-table-ids",
                                     "api-get-worksheet-underlying-logical-table-data (columns only)",
                                     "set-parameter-value", "export-view-data-underlying-to-csv-server"]},
            "session": {"id_hash": tg.ts.get("sessionIdHash"), "server_version": tg.ts.get("externalVersion"),
                        "workbook_last_published": tg.ts.get("workbookLastPublishedAt"),
                        "seconds": round(time.time() - t0, 1)},
            "tables": tables, "unexpected_tables": unexpected}


def month_windows(first: date, last: date):
    """Monthly windows (the card's cadence). The export has no row cap, so this only limits per-call size."""
    d = first.replace(day=1)
    while d <= last:
        nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        yield max(d, first), min(nxt - timedelta(days=1), last)
        d = nxt
