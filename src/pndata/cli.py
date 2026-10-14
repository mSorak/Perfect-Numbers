"""The `pn` command-line tool."""

from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone

import duckdb
import typer

from pndata import __version__
from pndata.config import DATA_ROOT_LAYERS, KEYS_FILE, data_root, load_keys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(no_args_is_help=True, help="Perfect Numbers data hub")

KNOWN_KEYS = ("IPUMS_API_KEY", "CENSUS_API_KEY", "BLS_API_KEY", "FRED_API_KEY",
              "DATA_GOV_API_KEY", "HUD_API_TOKEN", "SOCRATA_APP_TOKEN", "WMATA_API_KEY")
NEEDED_SOON = ("CENSUS_API_KEY", "BLS_API_KEY", "IPUMS_API_KEY")


@app.command()
def doctor() -> None:
    """Check the data root, keys file and DuckDB version (key values are never shown)."""
    ok = True
    typer.echo(f"pndata {__version__} · duckdb {duckdb.__version__}")
    if tuple(int(x) for x in duckdb.__version__.split(".")[:2]) < (1, 5):
        typer.echo("  ✗ DuckDB >= 1.5 required")
        ok = False
    root = data_root()
    missing = [layer for layer in DATA_ROOT_LAYERS if not (root / layer).is_dir()]
    typer.echo(f"data root: {root}" + ("" if not missing else f"  ✗ missing: {', '.join(missing)}"))
    ok &= not missing
    keys = load_keys()
    typer.echo(f"keys file: {KEYS_FILE}" + ("" if KEYS_FILE.exists() else "  ✗ not found"))
    for name in KNOWN_KEYS:
        mark = "set" if name in keys else ("MISSING (needed soon)" if name in NEEDED_SOON else "not set")
        typer.echo(f"  {name:<20} {mark}")
    raise typer.Exit(code=0 if ok else 1)


@app.command()
def version() -> None:
    """Print the pndata version."""
    typer.echo(__version__)


@app.command()
def fetch(source_id: str, entity: list[str] = typer.Option(None, "--entity", "-e", help="Only these entities")) -> None:
    """Fetch a source's entities into immutable raw snapshots (skips unchanged)."""
    from pndata.cards import source_cards
    from pndata.connectors import CONNECTORS
    from pndata.manifest import commit_snapshot

    src = source_cards().get(source_id)
    if not src:
        raise typer.BadParameter(f"no source card {source_id!r}")
    for name, cfg in src["entities"].items():
        if entity and name not in entity:
            continue
        if cfg.get("connector") == "manual":
            typer.echo(f"- {source_id}/{name}: manual source; use `pn intake`")
            continue
        work = data_root() / "tmp" / f"fetch_{source_id}_{name}_{datetime.now(timezone.utc):%H%M%S}"
        work.mkdir(parents=True)
        try:
            meta = CONNECTORS[cfg["connector"]](cfg, work)
            rec = commit_snapshot(work, source_id, name, meta, period=cfg.get("period"))
        except Exception:
            shutil.rmtree(work, ignore_errors=True)
            raise
        if rec is None:
            typer.echo(f"= {source_id}/{name}: unchanged since last snapshot")
        else:
            rows = f", {rec['rows']:,} rows" if rec.get("rows") else ""
            typer.echo(f"✓ {source_id}/{name}: snapshot {rec['snapshot_id']}{rows}")


@app.command()
def intake(source_id: str,
           period: str = typer.Option(..., "--period", "-p", help="Batch period: 2025H2, 2025Q3, 2025-07 or 2025"),
           files: list[str] = typer.Argument(None, help="Files to intake; default: everything in inbox/<source>/"),
           copy: bool = typer.Option(False, "--copy", help="Copy the files (legacy/archive); never move or delete them"),
           retrieved_at: str = typer.Option(None, help="Export time (ISO, local if no offset); default: file mtime"),
           ui: str = typer.Option(None, help="UI settings used for the export, recorded in the manifest"),
           waive: list[str] = typer.Option(None, "--waive", help="Waiver code declared in the source card"),
           note: str = typer.Option(None, "--note", help="Note recorded in the manifest (required with --waive: why it applies)"),
           no_reconcile: bool = typer.Option(False, "--no-reconcile", help="Skip the publisher reconciliation"),
           dry_run: bool = typer.Option(False, "--dry-run", help="Run checks only; commit nothing")) -> None:
    """Check manually downloaded files and commit them as raw snapshots (one per entity)."""
    from pathlib import Path

    from pndata.cards import source_cards
    from pndata.intake import IntakeError
    from pndata.intake import intake as run_intake

    src = source_cards().get(source_id)
    if not src:
        raise typer.BadParameter(f"no source card {source_id!r}")
    if waive and not note:
        raise typer.BadParameter("--waive needs --note explaining why")
    when = None
    if retrieved_at:
        when = datetime.fromisoformat(retrieved_at)
        when = when if when.tzinfo else when.astimezone()
    try:
        run_intake(src, period, [Path(f) for f in files or []], copy=copy, retrieved_at=when, ui=ui,
                   waivers=waive, waiver_note=note, reconcile=not no_reconcile, dry_run=dry_run, log=typer.echo)
    except IntakeError as e:
        typer.echo(f"✗ {e}")
        raise typer.Exit(code=1)


@app.command()
def build(dataset_ids: list[str],
          upstream: bool = typer.Option(False, "--upstream", help="Also build dependencies first"),
          downstream: bool = typer.Option(False, "--downstream", help="Also rebuild dependents")) -> None:
    """Build datasets (runs tests; promotes only if no error-level check fails)."""
    from pndata.build import build_one, downstream_of, topo_order
    from pndata.cards import resolve_glob
    ids = [i for pat in dataset_ids for i in resolve_glob(pat)]
    order = topo_order(ids, upstream=upstream)
    if downstream:
        order = topo_order(order + [d for d in downstream_of(order) if d not in order], upstream=False)
    failed = []
    for i in order:
        rec = build_one(i, log=typer.echo)
        if rec["status"] != "ok":
            failed.append(i)
            break
    raise typer.Exit(code=1 if failed else 0)


@app.command()
def check(dataset_ids: list[str] = typer.Argument(None, help="Dataset ids or globs; default: all")) -> None:
    """Re-run tests against current builds without rebuilding."""
    from pndata.build import column_doc_check, run_tests
    from pndata.builds import current_build
    from pndata.cards import dataset, resolve_glob
    from pndata.db import new_connection
    bad = 0
    from pndata.cards import dataset_cards
    ids = [i for p in dataset_ids for i in resolve_glob(p)] if dataset_ids else sorted(dataset_cards())
    for i in ids:
        card, cur = dataset(i), current_build(dataset(i))
        if not cur:
            typer.echo(f"✗ {i}: not built")
            bad += 1
            continue
        con = new_connection()
        con.execute(f"CREATE VIEW _this AS FROM read_parquet('{cur['path']}')")
        results = column_doc_check(con, card, "_this") + run_tests(con, card, "_this")
        for r in results:
            mark = "✓" if r.passed else ("✗" if r.severity == "error" else "!")
            typer.echo(f"{mark} {i} {r.name} {'' if r.passed else r.detail}")
            bad += (not r.passed and r.severity == "error")
    raise typer.Exit(code=1 if bad else 0)


@app.command()
def catalog() -> None:
    """Regenerate catalog.sql (views + comments) and docs in catalog/generated/."""
    from pndata.catalog import write_catalog
    written = write_catalog()
    typer.echo(f"✓ catalog.sql + {len(written)} dataset pages written")


@app.command()
def describe(dataset_id: str) -> None:
    """Print a dataset's generated page."""
    import pndata
    pndata.describe(dataset_id)


@app.command()
def status() -> None:
    """Sources: last snapshot. Datasets: current build and whether inputs are newer."""
    from pndata.builds import current_build
    from pndata.cards import dataset_cards, source_cards
    from pndata.manifest import latest_snapshot, read_manifest
    manifest = read_manifest()
    typer.echo("SOURCES")
    for sid, s in sorted(source_cards().items()):
        for ent in s["entities"]:
            rec = latest_snapshot(sid, ent)
            periods = sorted({r["period"] for r in manifest
                              if r["source_id"] == sid and r["entity"] == ent and r.get("period")})
            info = (f"{len(periods)} periods {periods[0]}..{periods[-1]}, last pull {rec['retrieved_at'][:10]}"
                    if periods else rec["snapshot_id"] if rec else "never fetched")
            typer.echo(f"  {sid}/{ent:<28} {info}")
    typer.echo("DATASETS")
    for cid, card in sorted(dataset_cards().items()):
        cur = current_build(card)
        if not cur:
            typer.echo(f"  {cid:<40} not built")
            continue
        stale = []
        for key, sid in cur["inputs"].get("raw", {}).items():
            src, ent = key.split("/", 1)
            latest = latest_snapshot(src, ent)
            if latest and latest["snapshot_id"] != sid:
                stale.append(key)
        for dep, bid in cur["inputs"].get("datasets", {}).items():
            dc = current_build(dataset_cards()[dep])
            if dc and dc["build_id"] != bid:
                stale.append(dep)
        typer.echo(f"  {cid:<40} {cur['build_id']} {cur['rows']:>10,}" + (f"  STALE: {', '.join(stale)}" if stale else ""))


if __name__ == "__main__":
    app()
