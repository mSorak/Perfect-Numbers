"""The build runner: card → SQL/Python/seed → Parquet build → tests → promote."""

from __future__ import annotations

import importlib.util
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from pndata import __version__
from pndata.builds import build_file, current_build, dataset_dir, posix
from pndata.cards import dataset, dataset_cards, dataset_deps
from pndata.config import REPO_ROOT, SEEDS_DIR
from pndata.db import new_connection
from pndata.manifest import git_sha, latest_snapshot, snapshot_dir, utc_now

KEEP_BUILDS = 5
PLACEHOLDER = re.compile(r"\{(raw|seed):([^}]+)\}")


@dataclass
class TestResult:
    name: str
    severity: str
    passed: bool
    detail: str = ""


@dataclass
class BuildContext:
    card: dict
    raw_inputs: dict = field(default_factory=dict)  # "source/entity" -> manifest record

    def raw(self, key: str) -> Path:
        """Path of the latest committed snapshot for 'source/entity'."""
        if key not in self.raw_inputs:
            source, entity = key.split("/", 1)
            rec = latest_snapshot(source, entity)
            if rec is None:
                raise FileNotFoundError(f"no raw snapshot for {key}; run `pn fetch {source}`")
            self.raw_inputs[key] = rec
        return snapshot_dir(self.raw_inputs[key])

    def raw_set(self, key: str, grain: str, periods: list[str] | None = None) -> list[Path]:
        """Data files of the newest snapshot per period (see manifest.select_snapshots); `_` files excluded."""
        from pndata.manifest import select_snapshots
        source, entity = key.split("/", 1)
        recs = select_snapshots(source, entity, grain, periods)
        if not recs:
            raise FileNotFoundError(f"no {grain} snapshots for {key}")
        self.raw_inputs[key] = recs
        return [snapshot_dir(r) / f["name"] for r in recs for f in r["files"] if not f["name"].startswith("_")]

    def seed(self, name: str) -> Path:
        return SEEDS_DIR / name


def topo_order(ids: list[str], upstream: bool) -> list[str]:
    order, seen = [], set()

    def visit(i):
        if i in seen:
            return
        seen.add(i)
        if upstream:
            for d in dataset_deps(dataset(i)):
                visit(d)
        order.append(i)
    for i in ids:
        visit(i)
    return order


def downstream_of(ids: list[str]) -> list[str]:
    cards = dataset_cards()
    out, frontier = set(ids), set(ids)
    while frontier:
        nxt = {cid for cid, c in cards.items() if set(dataset_deps(c)) & frontier} - out
        out |= nxt
        frontier = nxt
    full = topo_order(sorted(out), upstream=True) if out else []
    return [i for i in full if i in out]  # dependency order, but only the requested set and its dependents


def attach_dependencies(con: duckdb.DuckDBPyConnection, card: dict) -> dict:
    used = {}
    for dep in dataset_deps(card):
        dc = dataset(dep)
        cur = current_build(dc)
        if cur is None:
            raise RuntimeError(f"{card['id']} depends on {dep}, which has no build; run `pn build {dep}`")
        schema, name = dep.split(".", 1)
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        con.execute(f"CREATE OR REPLACE VIEW {dep} AS FROM read_parquet('{cur['path']}')")
        used[dep] = cur["build_id"]
    return used


def render_sql(sql: str, ctx: BuildContext) -> str:
    def sub(m):
        kind, key = m.groups()
        return posix(ctx.raw(key)) if kind == "raw" else posix(ctx.seed(key))
    return PLACEHOLDER.sub(sub, sql)


def produce_relation(con, card: dict, ctx: BuildContext) -> str:
    """Return a SQL query string producing the dataset."""
    b = card["build"]
    if "sql" in b:
        return render_sql((REPO_ROOT / b["sql"]).read_text(encoding="utf-8"), ctx)
    if "seed" in b:
        return f"FROM read_csv('{posix(ctx.seed(b['seed']))}', header=true, all_varchar={str(b.get('all_varchar', False)).lower()})"
    if "python" in b:
        file, func = b["python"].split(":")
        spec = importlib.util.spec_from_file_location(f"pipeline_{card['id']}", REPO_ROOT / file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = getattr(mod, func)(con, ctx)
        if isinstance(result, str):
            return result
        con.register("_python_result", result)
        return "FROM _python_result"
    raise ValueError(f"{card['id']}: build needs sql, python or seed")


def run_tests(con, card: dict, view: str) -> list[TestResult]:
    results = []
    for t in card.get("tests", []):
        sev = t.get("severity", "error")
        if "unique" in t:
            cols = t["unique"] if isinstance(t["unique"], list) else [t["unique"]]
            n = con.sql(f"SELECT count(*) FROM (SELECT {', '.join(cols)} FROM {view} GROUP BY ALL HAVING count(*) > 1)").fetchone()[0]
            results.append(TestResult(f"unique({','.join(cols)})", sev, n == 0, f"{n} duplicate keys"))
        elif "not_null" in t:
            for c in (t["not_null"] if isinstance(t["not_null"], list) else [t["not_null"]]):
                n = con.sql(f"SELECT count(*) FROM {view} WHERE {c} IS NULL").fetchone()[0]
                results.append(TestResult(f"not_null({c})", sev, n == 0, f"{n} nulls"))
        elif "accepted_values" in t:
            av = t["accepted_values"]
            vals = ", ".join(repr(v) for v in av["values"])
            n = con.sql(f"SELECT count(*) FROM {view} WHERE {av['column']} IS NOT NULL AND {av['column']} NOT IN ({vals})").fetchone()[0]
            results.append(TestResult(f"accepted_values({av['column']})", sev, n == 0, f"{n} unexpected values"))
        elif "row_count" in t:
            rc = t["row_count"]
            n = con.sql(f"SELECT count(*) FROM {view}").fetchone()[0]
            ok = n >= rc.get("min", 0) and n <= rc.get("max", float("inf"))
            results.append(TestResult("row_count", sev, ok, f"{n} rows (expected {rc})"))
        elif "relationships" in t:
            r = t["relationships"]
            to_card = dataset(r["to"])
            cur = current_build(to_card)
            target = f"read_parquet('{cur['path']}')" if cur else r["to"]
            field_to = r.get("field", r["column"])
            n = con.sql(f"SELECT count(*) FROM {view} v WHERE v.{r['column']} IS NOT NULL AND v.{r['column']} NOT IN (SELECT {field_to} FROM {target})").fetchone()[0]
            results.append(TestResult(f"relationships({r['column']}→{r['to']})", sev, n == 0, f"{n} orphans"))
        elif "sql" in t:
            sql = t["sql"].replace("{this}", view)
            rows = con.sql(sql).fetchall()
            results.append(TestResult(t.get("name", "sql"), sev, len(rows) == 0,
                                      f"{len(rows)} failing rows" + (f", e.g. {rows[0]}" if rows else "")))
    return results


def column_doc_check(con, card: dict, view: str) -> list[TestResult]:
    actual = [r[0] for r in con.sql(f"DESCRIBE {view}").fetchall()]
    documented = [c["name"] for c in card.get("columns", [])]
    undocumented = [c for c in actual if c not in documented]
    missing = [c for c in documented if c not in actual]
    sev = "error" if card.get("layer") == "mart" else "warn"
    out = []
    if undocumented:
        out.append(TestResult("columns_documented", sev, False, f"undocumented: {undocumented}"))
    if missing:
        out.append(TestResult("documented_columns_exist", "error", False, f"documented but missing: {missing}"))
    if not undocumented and not missing:
        out.append(TestResult("columns_documented", sev, True))
    return out


def prune(card: dict, keep: int = KEEP_BUILDS) -> None:
    files = sorted(dataset_dir(card).glob("build=*.parquet"))
    for f in files[:-keep]:
        f.unlink()


def build_one(dataset_id: str, log=print) -> dict:
    card = dataset(dataset_id)
    ctx = BuildContext(card)
    con = new_connection()
    deps_used = attach_dependencies(con, card)
    query = produce_relation(con, card, ctx)
    bid = utc_now().strftime("%Y%m%dT%H%M%SZ")
    out = build_file(card, bid)
    out.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({query}) TO '{posix(out)}' (FORMAT parquet, COMPRESSION zstd)")
    con.execute(f"CREATE OR REPLACE VIEW _this AS FROM read_parquet('{posix(out)}')")
    rows = con.sql("SELECT count(*) FROM _this").fetchone()[0]
    results = column_doc_check(con, card, "_this") + run_tests(con, card, "_this")
    failed = [r for r in results if not r.passed and r.severity == "error"]
    record = {
        "dataset_id": dataset_id, "build_id": bid, "path": posix(out), "rows": rows,
        "status": "failed" if failed else "ok",
        "inputs": {"datasets": deps_used,
                   "raw": {k: ([r["snapshot_id"] for r in v] if isinstance(v, list) else v["snapshot_id"])
                           for k, v in ctx.raw_inputs.items()}},
        "git_sha": git_sha(), "pn_version": __version__, "duckdb": duckdb.__version__,
        "tests": [r.__dict__ for r in results],
    }
    (out.parent / f"build={bid}.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    for r in results:
        if not r.passed:
            log(f"  {'✗' if r.severity == 'error' else '!'} {r.name}: {r.detail}")
    if failed:
        log(f"✗ {dataset_id}: {len(failed)} failing check(s); build {bid} NOT promoted")
        return record
    (out.parent / "_current.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    prune(card)
    log(f"✓ {dataset_id}: {rows:,} rows (build {bid})")
    return record
