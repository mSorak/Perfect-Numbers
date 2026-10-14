"""The `pn` command-line tool. Phase 0 provides `doctor`; later phases add fetch/intake/build/catalog."""

import duckdb
import typer

from pndata import __version__
from pndata.config import DATA_ROOT_LAYERS, KEYS_FILE, data_root, load_keys

app = typer.Typer(no_args_is_help=True, help="Perfect Numbers data hub")

KNOWN_KEYS = ("IPUMS_API_KEY", "CENSUS_API_KEY", "BLS_API_KEY", "FRED_API_KEY",
              "DATA_GOV_API_KEY", "HUD_API_TOKEN", "SOCRATA_APP_TOKEN", "WMATA_API_KEY")
NEEDED_SOON = ("CENSUS_API_KEY", "BLS_API_KEY", "IPUMS_API_KEY")


@app.command()
def doctor() -> None:
    """Check the data root, keys file and DuckDB version (key values are never shown)."""
    ok = True
    typer.echo(f"pndata {__version__} · duckdb {duckdb.__version__}")
    major, minor = (int(x) for x in duckdb.__version__.split(".")[:2])
    if (major, minor) < (1, 5):
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
