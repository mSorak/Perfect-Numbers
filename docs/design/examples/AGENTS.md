# AGENTS.md — Perfect Numbers data hub  (DRAFT — proposed root file; not active yet)

> Instructions for any AI coding agent (Claude Code, Codex, Cursor, Copilot, Gemini…) working in this repo.
> Claude Code loads this via `CLAUDE.md` containing the single line `@AGENTS.md`. Keep this file short; details live in linked docs.

## What this repo is
Analysis and writing for the *Perfect Numbers* blog (Maryland transportation, housing, politics).
This repo **is** the data hub (pipeline-first): code in `src/pndata`, dataset cards in `catalog/`, build logic in `pipelines/`.
Bytes live in the data root `$env:PN_DATA_ROOT` (default `C:\Users\Matt\pn-data` on the dev PC, outside OneDrive and git).
Piece-specific code lives in `projects/<slug>/` only when worth keeping.

## The five rules
1. **Query hub data by dataset ID** (`crash.report_cost`, `geo.tract`, `census.acs5`, …). Never copy hub files into a project folder — filter in the query. Declare what you use in the project's `project.yml`.
2. **Never modify the data root's append-only layers** (`raw/`, `cache/`, `docs/`, `packs/`). Raw files are read-only evidence; note that a "read-only" DuckDB session can still write files with `COPY … TO`, so don't.
3. **Add or refresh data only with the `pn` CLI**, which writes manifests and runs checks. If a check fails, stop and report — never `--force` without Matt's explicit OK.
4. **State vintage and time window** for every number you produce (e.g. "ACS 2020–24 5-year", "crashes, calendar 2025"). Use the metric macros in `catalog/metrics.sql` (definitions in `metrics.md`) for rates, VMT exposure and inflation.
5. **Secrets and personal data:** API keys live in `%USERPROFILE%\.config\pn\.env` — never print, copy or commit them, and redact them from URLs. Columns tagged `pii` (crash-person demographics, crime-victim fields, licence plates, GPS traces) never go into published outputs.

## Find data
- Start at `catalog/generated/CATALOG.md` (one line per dataset) → `catalog/generated/datasets/<id>.md` (grain, keys, columns, caveats, coverage, lineage).
- `pn describe <id>` prints the same card; `pn status` shows freshness and anything stale.
- Example queries (question first): `queries/examples/*.sql`.
- SQL from a terminal: `duckdb -init "$env:PN_DATA_ROOT\catalog.sql"` — views plus column descriptions (see `duckdb_columns()` comments).

## Use data in an analysis
```python
import pndata as pn
con = pn.connect(project="projects/crash_costs")      # in-memory DuckDB + catalog.sql; honours the project's pins
df = con.sql("""
    select county_geoid, sum(cost_total_usd2025) as cost_usd2025
    from crash.report_cost where year = 2025 group by 1
""").df()
tracts = pn.read_geo("geo.tract", vintage=2024, where="county_geoid = '24031'")
acs = pn.census.acs5("B25034", geo="tract", state="24", county="031", vintage=2024)   # cache-through
```
Exploring: data floats on current builds. Drafting: `pn pin projects/<slug>`. Publishing: register outputs with `pn.publish(df, name=..., chart=...)`, then `pn pack <post_slug> --project projects/<slug>`.

## Add a new dataset
Follow `catalog/conventions.md` and the intake standard (proposal §5.3): source card → access mode → scope (MD by default) →
`pn fetch`/`pn intake` → staging SQL → card documenting every mart column → tests incl. one domain sanity check →
backbone joins (`geoid`, `person_id`) → example query → `pn check <id>` passes. Only add datasets a piece needs.

## Commands
`pn status` · `pn fetch <source_id>` · `pn intake <source_id> --period …` · `pn build <id> --upstream --downstream` · `pn check <id>` · `pn catalog` · `pn describe <id>` · `pn export app:<name>` · `pn pin <project>` · `pn pack <slug> --project <path>`
(`pn` is installed with `uv tool install --editable .` from the repo root, so it works from any folder.)

## Conventions (short)
snake_case · `geoid` text zero-padded + `geoid_vintage` · `report_number` (ACRS) · money `*_usd<year>` · `year`/`month`/`date` for what a row describes, `vintage` for the edition — no "current" columns · store OGC:CRS84, measure in EPSG:26985 (metres) · `*_display` geometry is for maps only.

## Don't
- Don't hand-edit `catalog/generated/` — run `pn catalog`.
- Don't use positional or name-based keys after staging.
- Don't mix seasonally adjusted and unadjusted series, or different ACS/PEP vintages, without labelling.
- Don't download national files when Maryland files exist (tract/block group/place are per-state; county/ZCTA are national — filter at intake).
