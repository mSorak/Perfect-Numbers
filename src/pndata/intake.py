"""Manual intake: files downloaded by hand → checked, immutable raw snapshots (`pn intake`).

A batch is the set of files for one source and one period (e.g. the four MDSP tabs for 2025H2).
Each file's entity is detected by header signature (from the source card). All checks run on a
staged copy before anything is committed; an error-level check stops the whole batch unless a
waiver declared in the source card covers it. Files in the inbox are moved (deleted from the inbox
after commit); files given with --copy are copied and the originals are never touched.
"""

from __future__ import annotations

import csv
import io
import re
import shutil
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import duckdb
import requests

from pndata.config import USER_AGENT, data_root
from pndata.manifest import commit_snapshot, sha256_file


# ---------- periods ----------

def parse_period(period: str) -> tuple[date, date]:
    """'2025H2' / '2025Q3' / '2025-07' / '2025' → (first day, last day)."""
    if m := re.fullmatch(r"(\d{4})H([12])", period):
        y, h = int(m[1]), int(m[2])
        return (date(y, 1, 1), date(y, 6, 30)) if h == 1 else (date(y, 7, 1), date(y, 12, 31))
    if m := re.fullmatch(r"(\d{4})Q([1-4])", period):
        y, q = int(m[1]), int(m[2])
        start = date(y, 3 * q - 2, 1)
        end = date(y + (q == 4), (3 * q) % 12 + 1, 1) - timedelta(days=1)
        return start, end
    if m := re.fullmatch(r"(\d{4})-(\d{2})", period):
        y, mo = int(m[1]), int(m[2])
        return date(y, mo, 1), date(y + (mo == 12), mo % 12 + 1, 1) - timedelta(days=1)
    if re.fullmatch(r"\d{4}", period):
        return date(int(period), 1, 1), date(int(period), 12, 31)
    raise ValueError(f"unrecognised period {period!r}; use 2025H2, 2025Q3, 2025-07 or 2025")


# ---------- checks ----------

@dataclass
class Check:
    name: str
    status: str  # pass | warn | fail | waived
    detail: str = ""
    value: object = None
    waiver: str | None = None

    def record(self) -> dict:
        out = {"status": self.status}
        if self.value is not None:
            out["value"] = self.value
        if self.detail:
            out["detail"] = self.detail
        if self.waiver:
            out["waiver"] = self.waiver
        return out


@dataclass
class Item:
    entity: str
    src: Path
    work: Path
    retrieved_at: datetime
    rows: int = 0
    columns: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


def read_header(path: Path) -> list[str]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f), [])


def detect_entity(header: list[str], entities: dict) -> str | None:
    cols = set(header)
    hits = [name for name, cfg in entities.items()
            if cfg.get("header_signature") and set(cfg["header_signature"]) <= cols]
    if len(hits) > 1:
        raise RuntimeError(f"header matches several entities: {hits}")
    return hits[0] if hits else None


def _q(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def _rel(path: Path) -> str:
    return f"read_csv('{path.as_posix()}', all_varchar=true, header=true)"


# ---------- intake ----------

def intake(source: dict, period: str, files: list[Path] | None = None, copy: bool = False,
           retrieved_at: datetime | None = None, retrieved_at_method: str | None = None,
           ui: str | None = None, waivers: list[str] | None = None, waiver_note: str | None = None,
           reconcile: bool = True, dry_run: bool = False, entity: str | None = None,
           expected: dict[str, str] | None = None, extra_meta: dict | None = None,
           log=print) -> list[dict]:
    """Check and commit one batch. Returns the manifest records (empty on dry run or if all unchanged).

    `entity` skips header detection (one file only); non-CSV files get only the batch-level checks.
    `expected` (file name → entity, from a connector) must agree with header detection.
    `extra_meta` is merged into every manifest record (e.g. connector session info)."""
    source_id = source["source_id"]
    entities = source["entities"]
    cfg = source.get("intake", {})
    start, end = parse_period(period)
    inbox = data_root() / "inbox" / source_id
    if not files:
        if copy:
            raise ValueError("--copy needs explicit files")
        files = sorted(p for p in inbox.iterdir() if p.is_file()) if inbox.is_dir() else []
    if not files:
        raise ValueError(f"no files given and nothing in {inbox}")
    if entity and (entity not in entities or len(files) != 1):
        raise ValueError(f"--entity needs exactly one file and one of {sorted(entities)}")
    waivers = waivers or []
    for w in waivers:
        if w not in cfg.get("waivers", {}):
            raise ValueError(f"unknown waiver {w!r}; the source card declares {sorted(cfg.get('waivers', {}))}")

    stage = data_root() / "tmp" / f"intake_{source_id}_{period}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
    items: dict[str, Item] = {}
    try:
        for f in files:
            f = Path(f)
            ent = entity or detect_entity(read_header(f), entities)
            if ent is None:
                raise RuntimeError(f"{f.name}: header matches no entity of {source_id}; check the export "
                                   f"or add a header_signature to the source card")
            if expected and expected.get(f.name) not in (None, ent):
                raise RuntimeError(f"{f.name}: connector says {expected[f.name]}, header says {ent}")
            if ent in items:
                raise RuntimeError(f"{f.name} and {items[ent].src.name} are both {ent}")
            work = stage / ent
            work.mkdir(parents=True)
            shutil.copy2(f, work / f.name)
            if sha256_file(work / f.name) != sha256_file(f):
                raise RuntimeError(f"{f.name}: copy hash mismatch")
            when = retrieved_at or datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)
            items[ent] = Item(ent, f, work / f.name, when)

        missing = [] if entity else [e for e, c in entities.items() if c.get("required", True) and e not in items]
        checks = _run_checks(source, items, start, end, missing, cfg)
        if reconcile and cfg.get("reconcile"):
            _reconcile(cfg["reconcile"], items, start, end, log)

        failed = _apply_waivers(items, checks, cfg.get("waivers", {}), waivers, waiver_note)
        for it in items.values():
            for c in it.checks:
                mark = {"pass": "✓", "warn": "!", "fail": "✗", "waived": "~"}[c.status]
                log(f"  {mark} {it.entity:<14} {c.name:<22} {c.detail}")
        for c in checks:
            mark = {"pass": "✓", "warn": "!", "fail": "✗", "waived": "~"}[c.status]
            log(f"  {mark} {'(batch)':<14} {c.name:<22} {c.detail}")
        if failed:
            raise IntakeError(f"{source_id} {period}: {len(failed)} check(s) failed: "
                              + ", ".join(failed) + ". Nothing was committed.")
        if dry_run:
            log("dry run: nothing committed")
            return []

        batch_checks = {c.name: c.record() for c in checks}
        session_id = f"{min(it.retrieved_at for it in items.values()):%Y%m%dT%H%MZ}"
        records = []
        for ent, it in items.items():
            meta = {
                "method": "manual",
                "original_filename": it.src.name,
                "original_path": str(it.src) if copy else None,
                "retrieved_at_method": retrieved_at_method or (
                    "given on the command line" if retrieved_at else
                    "file mtime (legacy intake)" if copy else "file mtime"),
                "request": {**({"ui": ui} if ui else {}), **(cfg.get("request") or {}),
                            "period_start": start.isoformat(), "period_end": end.isoformat()},
                "rows": it.rows, "columns": len(it.columns),
                "session_id": session_id,
                "intake_checks": {**{c.name: c.record() for c in it.checks}, **batch_checks},
                **it.extra,
                **(extra_meta or {}),
            }
            if waivers:
                meta["waivers"] = [{"code": w, "note": waiver_note} for w in waivers]
            elif waiver_note:
                meta["note"] = waiver_note
            if _same_content(source_id, ent, period, it):
                log(f"= {source_id}/{ent} {period}: same rows as the existing snapshot (row order differs)")
                continue
            rec = commit_snapshot(it.work.parent, source_id, ent, meta, period=period,
                                  retrieved_at=it.retrieved_at)
            if rec is None:
                log(f"= {source_id}/{ent} {period}: identical to the existing snapshot")
            else:
                log(f"✓ {source_id}/{ent}: {rec['snapshot_id']}" + (f", {it.rows:,} rows" if it.rows else ""))
                records.append(rec)
        if not copy:
            for it in items.values():
                it.src.unlink()
        return records
    finally:
        shutil.rmtree(stage, ignore_errors=True)


class IntakeError(RuntimeError):
    pass


def _same_content(source_id: str, entity: str, period: str, it: Item) -> bool:
    """True if the latest snapshot of this period has the same columns and the same rows (as a multiset).
    Some exports (Tableau) reorder rows between identical pulls; that must not create a new snapshot."""
    from pndata.manifest import latest_snapshot, snapshot_dir
    prev = latest_snapshot(source_id, entity, period)
    if prev is None or it.work.suffix.lower() != ".csv":
        return False
    old = [f for f in prev["files"] if not Path(f["name"]).name.startswith("_")]
    if len(old) != 1 or not old[0]["name"].lower().endswith(".csv"):
        return False
    old_path = snapshot_dir(prev) / old[0]["name"]
    if old[0]["sha256"] == sha256_file(it.work):
        return False  # byte-identical: commit_snapshot skips it and says so
    if sorted(read_header(old_path)) != sorted(it.columns):
        return False
    a, b = _rel(old_path), _rel(it.work)
    cols = ", ".join(_q(c) for c in sorted(it.columns))
    con = duckdb.connect()
    diff = con.execute(f"SELECT (SELECT count(*) FROM (SELECT {cols} FROM {a} EXCEPT ALL SELECT {cols} FROM {b})) + "
                       f"(SELECT count(*) FROM (SELECT {cols} FROM {b} EXCEPT ALL SELECT {cols} FROM {a}))").fetchone()[0]
    return diff == 0


def _run_checks(source: dict, items: dict[str, Item], start: date, end: date, missing: list[str],
                cfg: dict) -> list[Check]:
    entities = source["entities"]
    con = duckdb.connect()
    for entity, it in items.items():
        ecfg = entities[entity]
        if it.work.suffix.lower() != ".csv":
            it.checks.append(Check("file", "pass", f"{it.work.stat().st_size:,} bytes; not CSV, content checks skipped"))
            continue
        it.columns = read_header(it.work)
        con.execute(f"CREATE VIEW {_q(entity)} AS FROM {_rel(it.work)}")
        it.rows = con.execute(f"SELECT count(*) FROM {_q(entity)}").fetchone()[0]
        it.checks.append(Check("header_signature", "pass", f"{len(it.columns)} columns"))
        it.checks.append(Check("rows", "pass" if it.rows else "fail", f"{it.rows:,}", it.rows))
        if key := ecfg.get("key"):
            # Exact duplicate rows (the same record exported twice upstream) are a warning; a key whose rows
            # disagree, or a null key, is an error.
            cols, t = ", ".join(_q(c) for c in key), _q(entity)
            n_null, n_exact, n_conflict = con.execute(
                f"SELECT (SELECT count(*) FROM {t} WHERE " + " OR ".join(f"{_q(c)} IS NULL" for c in key) + "), "
                f"(SELECT count(*) FROM {t}) - (SELECT count(*) FROM (SELECT DISTINCT * FROM {t})), "
                f"(SELECT count(*) FROM (SELECT {cols} FROM (SELECT DISTINCT * FROM {t}) GROUP BY ALL HAVING count(*) > 1))"
            ).fetchone()
            status = "fail" if n_null or n_conflict else "warn" if n_exact else "pass"
            it.checks.append(Check("key_unique", status,
                                   f"{'+'.join(key)}: {n_null} null, {n_conflict} conflicting, "
                                   f"{n_exact} exact duplicate rows",
                                   {"null": n_null, "conflicting": n_conflict, "exact_duplicate_rows": n_exact}))
        if dc := ecfg.get("date_column"):
            fmt = ecfg.get("date_format", "%Y-%m-%d")
            lo, hi, bad = con.execute(
                f"SELECT min(d), max(d), count(*) FILTER (WHERE d IS NULL AND raw IS NOT NULL) FROM "
                f"(SELECT {_q(dc)} AS raw, try_strptime({_q(dc)}, '{fmt}')::DATE AS d FROM {_q(entity)})"
            ).fetchone()
            outside = con.execute(
                f"SELECT count(*) FROM (SELECT try_strptime({_q(dc)}, '{fmt}')::DATE AS d FROM {_q(entity)}) "
                f"WHERE d < DATE '{start}' OR d > DATE '{end}'").fetchone()[0]
            status = "fail" if bad or outside or lo is None else "pass"
            it.checks.append(Check("dates_in_period", status,
                                   f"{dc} {lo}..{hi}, {outside} outside {start}..{end}, {bad} unparsed",
                                   {"min": str(lo), "max": str(hi), "outside": outside, "unparsed": bad}))
        if parent := ecfg.get("parent"):
            p_ent = parent["entity"]
            if p_ent not in items:
                it.checks.append(Check("orphans", "warn", f"parent {p_ent} not in this batch; not checked"))
            else:
                ck, pk = _q(parent["key"]), _q(parent["parent_key"])
                n_child, n_orphan = con.execute(
                    f"SELECT count(DISTINCT c.{ck}), count(DISTINCT c.{ck}) FILTER (WHERE p.{pk} IS NULL) "
                    f"FROM {_q(entity)} c LEFT JOIN {_q(p_ent)} p ON c.{ck} = p.{pk}").fetchone()
                pct = round(100 * n_orphan / n_child, 3) if n_child else 0.0
                limit = parent.get("max_orphan_pct", 0.0)
                it.checks.append(Check("orphans", "pass" if pct <= limit else "fail",
                                       f"{n_orphan} of {n_child:,} {parent['key']} not in {p_ent} ({pct}%, limit {limit}%)",
                                       {"value": n_orphan, "pct": pct}))
                n_parent = con.execute(f"SELECT count(*) FROM {_q(p_ent)}").fetchone()[0]
                it.extra[f"{entity}_per_{p_ent}"] = round(it.rows / n_parent, 3) if n_parent else None

    batch = []
    batch.append(Check("entities_present", "fail" if missing else "pass",
                       f"missing: {', '.join(missing)}" if missing else ", ".join(items)))
    if cfg.get("same_session_hours") is not None and len(items) > 1:
        times = sorted((it.retrieved_at, e) for e, it in items.items())
        gap_h = (times[-1][0] - times[0][0]).total_seconds() / 3600
        limit = cfg["same_session_hours"]
        batch.append(Check("same_session", "pass" if gap_h <= limit else "fail",
                           f"exports span {gap_h:.1f} h ({times[0][1]} {times[0][0]:%Y-%m-%d %H:%M} → "
                           f"{times[-1][1]} {times[-1][0]:%Y-%m-%d %H:%M} UTC; limit {limit} h)", round(gap_h, 2)))
    return batch


def _apply_waivers(items: dict[str, Item], batch: list[Check], declared: dict, used: list[str],
                   note: str | None) -> list[str]:
    """Turn failing checks covered by a used waiver into 'waived'. Returns names of checks still failing."""
    covered = {c for w in used for c in declared[w].get("waives", [])}
    code_for = {c: w for w in used for c in declared[w].get("waives", [])}
    failed = []
    all_checks = [(it.entity, c) for it in items.values() for c in it.checks] + [("batch", c) for c in batch]
    for owner, c in all_checks:
        if c.status != "fail":
            continue
        if c.name in covered:
            c.status, c.waiver = "waived", f"{code_for[c.name]}: {note or declared[code_for[c.name]].get('description', '')}"
        else:
            failed.append(f"{owner}.{c.name}")
    return failed


def _reconcile(rc: dict, items: dict[str, Item], start: date, end: date, log) -> None:
    """Compare distinct-key counts per group against the publisher's own summary endpoint (warn only)."""
    it = items.get(rc["entity"])
    if it is None:
        return
    url = rc["url"].format(start=start.isoformat(), end=end.isoformat())
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
    except requests.RequestException as e:
        it.checks.append(Check("reconciliation", "warn", f"endpoint unavailable: {e}"))
        return
    (it.work.parent / "_reconciliation.csv").write_bytes(r.content)
    rows = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
    count_col, groups = rc["count_column"], rc["group_by"]
    theirs: dict[tuple, int] = {}
    for row in rows:
        g = tuple(row[c] for c in groups)
        theirs[g] = theirs.get(g, 0) + int(row[count_col].replace(",", ""))
    con = duckdb.connect()
    key = _q(rc["key"])
    cols = ", ".join(_q(c) for c in groups)
    ours = {tuple(r[:-1]): r[-1] for r in con.execute(
        f"SELECT {cols}, count(DISTINCT {key}) FROM {_rel(it.work)} GROUP BY ALL").fetchall()}
    t_ours, t_theirs = sum(ours.values()), sum(theirs.values())
    diff_pct = round(100 * (t_ours - t_theirs) / t_theirs, 3) if t_theirs else None
    tol = rc.get("tolerance_pct", 0.5)
    worst = sorted(((g, ours.get(g, 0) - theirs.get(g, 0)) for g in set(ours) | set(theirs)),
                   key=lambda x: -abs(x[1]))[:5]
    status = "pass" if diff_pct is not None and abs(diff_pct) <= tol else "warn"
    it.checks.append(Check("reconciliation", status,
                           f"file {t_ours:,} vs endpoint {t_theirs:,} ({diff_pct:+}%, tolerance ±{tol}%)",
                           {"file": t_ours, "endpoint": t_theirs, "diff_pct": diff_pct,
                            "largest_group_diffs": [{"group": list(g), "diff": d} for g, d in worst if d]}))
    it.extra["reconciliation_url"] = url


# ---------- connector-driven batches (e.g. MDSP via tableau_public) ----------

def month_range(spec: str) -> list[str]:
    """'2026-09' → ['2026-09']; '2024-01:2026-09' → every month in between, inclusive."""
    lo, _, hi = spec.partition(":")
    hi = hi or lo
    (y, m), (y1, m1) = (map(int, lo.split("-")), map(int, hi.split("-")))
    out = []
    while (y, m) <= (y1, m1):
        out.append(f"{y}-{m:02d}")
        y, m = (y + (m == 12), m % 12 + 1)
    return out


def trailing_months(n: int, today: date | None = None) -> list[str]:
    """The last n complete calendar months before `today`."""
    d = (today or date.today()).replace(day=1)
    out = []
    for _ in range(n):
        d = (d - timedelta(days=1)).replace(day=1)
        out.append(f"{d:%Y-%m}")
    return sorted(out)


def fetch_batch(source: dict, period: str, log=print) -> list[dict]:
    """Run the source's batch connector for one period into tmp/, then check and commit via intake()."""
    from pndata.connectors import BATCH_CONNECTORS
    cfg = source["fetch"]
    start, end = parse_period(period)
    work = data_root() / "tmp" / f"fetch_{source['source_id']}_{period}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
    work.mkdir(parents=True)
    try:
        when = datetime.now(timezone.utc)
        meta = BATCH_CONNECTORS[cfg["connector"]]({**cfg, "start": start.isoformat(), "end": end.isoformat()}, work)
        if meta.get("unexpected_tables"):
            log(f"  ! upstream has tables the card doesn't list: {meta['unexpected_tables']}")
        expected = {t["file"]: ent for ent, t in meta["tables"].items()}
        files = [work / name for name in expected]
        return intake(source, period, files, copy=False, retrieved_at=when,
                      retrieved_at_method=f"{cfg['connector']} export (time the session started)",
                      expected=expected, extra_meta={k: meta[k] for k in ("method", "request", "session", "tables")},
                      log=log)
    finally:
        shutil.rmtree(work, ignore_errors=True)
