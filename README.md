# Perfect Numbers — data pipeline

The data hub behind [Perfect Numbers](https://perfectnumbers.substack.com/), a blog about transportation, housing and politics in Maryland.

This repo holds the **code, dataset catalog and documentation** for a local-first data pipeline: Maryland crash records and costs, traffic volumes, transit schedules and ridership, Census geography and tables, and more. Every dataset has a documented card, a stable name you can query, and a record of where each byte came from. The data itself lives outside git (see *Data root* below).

> **Status:** Phase 0 (setup), October 2026. The design is in [`docs/design/`](docs/design/README.md). Start with [`03_proposal.md`](docs/design/03_proposal.md) §0.

## Layout

| Path | What's there |
|---|---|
| `src/pndata/` | Python package and the `pn` command-line tool: connectors, build runner, checks |
| `catalog/datasets/` | One YAML **dataset card** per dataset, which is the source of truth for meaning, keys, columns and caveats |
| `catalog/sources/` | One card per publisher/endpoint: how to acquire, cadence, terms |
| `catalog/seeds/` | Small hand-maintained reference tables (CSV) |
| `catalog/manifests/` | `raw_manifest.jsonl`: every raw file ever acquired (URL, time, hash) |
| `catalog/generated/` | Generated docs (`CATALOG.md`, per-dataset pages). Don't edit by hand. |
| `pipelines/` | SQL/Python build steps referenced by the cards |
| `queries/examples/` | Question-first example queries |
| `projects/<slug>/` | Piece-specific analysis, only when it's worth keeping |
| `docs/` | Design documents and decision records |

## Data root

Data lives in `PN_DATA_ROOT` (default `C:\Users\Matt\pn-data`), outside git and OneDrive:
`raw/` (immutable source snapshots) → `staging/` → `marts/`, plus `cache/`, `docs/` and `packs/` (frozen data behind each published post).

## Setup (Windows)

```powershell
uv sync                        # creates .venv with pinned dependencies
uv run pn doctor               # checks the data root, keys file and DuckDB version
```

API keys go in `%USERPROFILE%\.config\pn\.env` (never in this repo).

## For AI agents

Read [`AGENTS.md`](AGENTS.md) first.
