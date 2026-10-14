# AGENTS.md — Perfect Numbers data hub

> Instructions for any AI coding agent (Claude Code, Claude Desktop, Cursor, Codex, local models…).
> Claude Code loads this through `CLAUDE.md` (`@AGENTS.md`). Keep this file short; details live in `docs/`.

## What this repo is
The data pipeline behind the *Perfect Numbers* blog (Maryland transportation, housing, politics). This repo **is** the data hub:
code in `src/pndata`, dataset cards in `catalog/`, build logic in `pipelines/`, design docs in `docs/design/`.
Data bytes live in the data root `$env:PN_DATA_ROOT` (default `C:\Users\Matt\pn-data`, on the dev PC, outside OneDrive and git).
Piece-specific code lives in `projects/<slug>/` only when worth keeping.

**Current status: Phase 0 (setup).** Only `pn doctor` and `pn version` exist. The design to build toward is
`docs/design/03_proposal.md` (§0.2 for recorded decisions; §10 for the roadmap). Don't invent commands that don't exist yet.

## The five rules
1. **Query hub data by dataset ID** (e.g. `crash.report_cost`). Never copy hub files into a project folder; filter in the query. Declare what a project uses in its `project.yml`.
2. **Never modify the data root's append-only layers** (`raw/`, `cache/`, `docs/`, `packs/`). Raw files are read-only evidence. A "read-only" DuckDB session can still write files with `COPY … TO`, so don't.
3. **Add or refresh data only through the `pn` CLI** once it exists. It writes manifests and runs checks. If a check fails, stop and report. Never `--force` without Matt's explicit OK.
4. **State vintage and time window** for every number you produce (e.g. "ACS 2020–24 5-year", "crashes, calendar 2025"). Use the metric definitions in `catalog/metrics.md` (when written) for rates, VMT exposure and inflation.
5. **Secrets and personal data.** API keys live in `%USERPROFILE%\.config\pn\.env`. Read them only through `pndata.config.get_key()`. Never print, copy or commit them, and redact them from logged URLs. Columns tagged `pii` (crash-person demographics, crime-victim fields, licence plates, GPS traces) never go into published outputs.

## Working here
- Environment: `uv sync`, then `uv run pn doctor`. Python 3.13, DuckDB `>=1.5.6,<2`.
- Data never goes in git: `.gitignore` blocks data extensions. The only allowed exceptions are seeds, manifests and design CSVs.
- New datasets follow the intake standard in `docs/design/03_proposal.md` §5.3. Only add datasets a piece needs.
- Conventions: snake_case · `geoid` as zero-padded text + `geoid_vintage` · `report_number` (ACRS) · money `*_usd<year>` · explicit `year`/`period` and `vintage` columns, no "current" columns · store OGC:CRS84, measure in EPSG:26985 (metres) · `*_display` geometry is for maps only.
- Don't download national files when per-state files exist (tract, block group and place are per-state; county and ZCTA are national-only, so filter them at intake).

## Commands that need Matt's explicit OK
- Pushing to GitHub, or changing branches or tags there.
- Deleting anything outside `$env:PN_DATA_ROOT\tmp`.
- Touching the archived OneDrive folder `C:\Users\Matt\OneDrive\personal\research\Perfect-Numbers`. It is read-only history.
