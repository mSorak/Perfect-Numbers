# Handoff: state of the data hub and how to start Phase 2

Last updated: 2026-10-14 (end of Phase 1). Read this after `AGENTS.md`. The full design is `docs/design/03_proposal.md`; Matt's decisions are in its §0.2 and in `docs/design/answers.md`.

## Where things are

| What | Where |
|---|---|
| Repo (pipeline-first) | `C:\Users\Matt\code\perfect-numbers` → GitHub `mSorak/Perfect-Numbers` (`main`). The old history is at tag `archive-2024-2026`. |
| Data root | `C:\Users\Matt\pn-data` (user env var `PN_DATA_ROOT`). On the dev PC only; not in git or OneDrive. |
| API keys | `C:\Users\Matt\.config\pn\.env`. IPUMS and Census are set; **BLS is missing** and Matt must add it before `econ.cpi_u`. Read keys only via `pndata.config.get_key()`. |
| Old project folders (read-only archive) | `C:\Users\Matt\OneDrive\personal\research\Perfect-Numbers\` (`2025/`, `2026/`). Don't modify anything there. Phase 2 inputs are read from it (below). |
| Nightly backup | Task Scheduler task "PN data backup" runs `ops/backup.ps1`. It copies only new files from raw/cache/docs/packs into `OneDrive\pn-data-backup`, at 2:30 AM. |

**This all lives on Matt's desktop PC.** A session must run on that machine (local Claude Code, or Remote Control attached to it) to see the data root, the archive and the keys. A cloud session sees only the GitHub repo.

## Phase 1 (done)

- **`pndata` package:** manifests, connectors (`http_file`, `arcgis`, `socrata`, `powerbi_public`), card-driven build runner with tests, catalog generator, `pn` CLI, and the line-to-street matcher `pndata/geo.py`.
- **19 datasets.** See `catalog/generated/CATALOG.md`. The marts are `transit.bus_segment_service` and `transit.bus_segment_summary`, for Matt's bus-lane piece. The `projects/baltimore_bus_lanes/project.yml` file declares what that piece uses.
- **Checks.** All pass. The one warning is expected: retired routes appear in the ridership history.
- **Fresh-agent usability test passed.**

## Phase 2: I-83 / ReVision Zero #3 slice (next)

Plan: `03_proposal.md` §10, "Phase 2". The work items, in order:

**Progress (2026-10-14):**
- **Item 1 is done.** `pn intake` is in `src/pndata/intake.py`, with tests in `tests/` (`uv run pytest`).
  - Checks: header signature, rows, key uniqueness, dates in period, orphan children, entities present, same session, and publisher reconciliation (warn-only).
  - Waivers are declared in the source card and recorded in the manifest along with `--note`.
- **Item 2: the card is written** (`catalog/sources/mdsp_acrs.yml`). The API-route spike is not started.
  - The reconciliation CSV also names the hidden tabs Contribs, Damage, Sequence and NMSafetyEquip. They are in the card as `required: false` until the first all-tabs export.
- **Item 3 is done.** 16 snapshots cover 2024H1–2025H2. All four reconciliations are within ±0.3%. 2025H2 carries the `legacy_mixed_session` waiver.
  - **Finding:** three legacy Vehicles files are mislabeled by half-year. `Vehicles_010124_063124` holds 2024H2, `Vehicles_070124_123124` holds 2025H1 and `Vehicles_010125_063125` holds 2024H1.
  - Each one matches 100% of one Reports file and 0% of the others. They were paired by content, and each manifest line has a `note` saying so.
  - The concatenated `*_maryland_2024_2025.csv` files cover all of them, so the legacy cost analysis is unaffected.
- **Next:** item 4 (staging cards). Read the half-years from the manifest by `period`, not by file name. Globs over a snapshot folder must skip `_`-prefixed files (e.g. `Reports_*.csv`, not `*.csv`; the reports folder holds `_reconciliation.csv`).

**More sources added (2026-10-14, second pass):**
- **`econ.cpi_u`** (source `bls`, connector `bls_api`). It holds CUUR0000SA0, CUSR0000SA0 and Baltimore CUURS35ESA0, 1975–2026-09.
  - June 2019 → June 2025 = 322.561 / 256.143 = **1.2593**.
  - October 2025 has no published value (shutdown).
- **Census ACS:** the `census_api` connector and its source card (`acs5_2024`, B01003, for state, county, place and tract) are written.
  - **Blocked:** the API rejects `CENSUS_API_KEY` as "Invalid Key". The key is well-formed, so it probably needs activating from the emailed link.
  - Then run `pn fetch census_api` and write the `census.acs5` staging card.
- **AADT** (source `mdot_sha_aadt`, stations and segments): `traffic.aadt_segment` (10,013) and `traffic.aadt_segment_year` (long, explicit years 2016–2025, with VMT).
  - The unsuffixed column = newest `AADT_<year>` + 1 = 2025, recorded in `year_method`.
  - Statewide ≈57B VMT in 2019; I-83 is 34.3 mi in Baltimore City and County.
- **FARS** (source `nhtsa_fars`, entity `national_csv`, `periods: 1975-2024`): all 50 national zips are fetched from static.nhtsa.gov.
  - 1975–2020 are byte-identical to the legacy zips.
  - NHTSA re-issued 2021–2023 on 2026-04-01. The legacy editions (used in pedestrian_deaths) were intaken as earlier snapshots with `pn intake --entity`.
  - Not staged yet (`crash.fars_*`, `ref.fars_codes`).
- **Seeds:** `ref.county_codes` (FIPS ↔ MDOT/ACRS alphabetical codes, verified against AADT and ACRS), `ref.nhtsa_unit_cost_2019` (Table 1-10, long format, with sum tests) and `ref.acrs_injury_to_mais` (map v1).
  - 8,089 occupants in 2025H1 have no injury status. Check how the legacy model treated them during parity work.
- **CLI:**
  - `pn fetch` supports per-period entities (`periods:` plus `{period}` in url and filename; `--period` to limit).
  - `pn intake --entity` covers non-CSV single files.
  - Tracebacks no longer print local variables, so keys can't leak.

**1. Build `pn intake`** (the `manual` connector). It isn't written yet. Requirements:
- Move files from `$PN_DATA_ROOT/inbox/<source>/` into `raw/<source>/<entity>/<snapshot_id>__<period>/`, read-only.
- Detect each file's entity by header signature.
- Record how `retrieved_at` was determined (file mtime for legacy files).
- Run the intake checks.

**2. Source card `mdsp_acrs`.** Use the draft in `docs/design/examples/source_card_example.yml`. Matt's decisions:
- Pull **all tables and all variables**.
- Prefer an **API route over Playwright** (do a time-boxed spike first).
- No bulk-access request.

**3. Intake the 16 legacy MDSP files.** Copy them; never move them out of the archive. They are in `2026\crash_costs\data\{Reports,Vehicles,Occupants,NonMotorists}\<Entity>_{010124_063124,070124_123124,010125_063125,070125_123125}.csv`.
- **Skip** the concatenated `*_maryland_2024_2025.csv` files.
- **Skip** `GitHubDesktopSetup-x64.exe` in the Vehicles folder.
- **2025-H2 is a mixed-session batch.** Reports were exported 2026-03-28 and Vehicles 2026-06-06, leaving 194 vehicle report numbers with no report. Record a `legacy_mixed_session` waiver for it.
- **Reconcile each half-year** against `https://analytics.mdsp.org/t/Public/views/PublicCrash2/PublicCrash.csv?Crash%20Date%20Begin=…&Crash%20Date%20End=…`. It returns county × severity distinct-report counts. H1-2025 was 49,332 there vs 49,373 in the file.

**4. Build the crash tables.**
- Staging: `crash.acrs_report`, `crash.acrs_vehicle`, `crash.acrs_person`. Draft card in `docs/design/examples/dataset_card_example.yml`.
- Then `crash.report_geo`, `crash.report_cost` (method 2026.1) and `crash.summary_*`.
- Unit costs: seed from `2026\crash_costs\tables_from_report.xlsx` (sheet `police_unit_costs_comp`).
- Injury map: 1→Fatal, 2→MAIS4, 3→MAIS2, 4→MAIS1, 5→MAIS0.
- Property-damage-only crashes are costed as vehicles × PDOVehicle.
- Deflator: CPI-U June 2019 → June 2025, with a `legacy_factor: 1.26` parameter for parity.

**5. Parity tests.**
- `crash.report_cost` must match `2026\crash_costs\data\crash_cost_eval.csv` row-for-row on the cost columns: 210,860 rows; 2024 = $41.044B; 2025 = $37.339B.
- Summaries must match `data\geo_summaries\merged_*.csv`.
- Pre-registered exit answer: Howard County 2025 cost per resident ≈ **$3,864** ($1.2995B ÷ 336,328, ACS 2020–24).
- Population comes from `census.acs5` (B01003, plus the other tables in `03` §10). This needs the `census_api` connector; the key is set.

**6. Corridor data for I-83.**
- AADT: `services.arcgis.com/njFNhDsUCentVYJW/.../MDOT_SHA_Annual_Average_Daily_Traffic/FeatureServer` layers 0 and 1. The "current" `AADT` column is ≈2025 in the October pull; assign it an explicit year.
- FARS: the zips for 1975–2023 already exist at `2025\pedestrian_deaths\data\fars\zips\`. FARS 2024 (Annual Report File) comes from `static.nhtsa.gov`.
- An I-83 / JFX corridor custom area.
- The Baltimore County crash MapServer as a cross-check.

**7. Do not touch the crash-cost app repo** (`2026\crash_costs\.git`). It has uncommitted edits Matt asked to leave alone. `pn export app:crash-cost-md` should write to a scratch folder for diffing until Matt says otherwise.

## Permissions and working agreements

- **Pushing to GitHub** needs Matt's OK each time (`AGENTS.md`). Ordinary fast-forward pushes work. Claude Code's auto mode blocks force pushes.
- **Never delete or modify** anything in the OneDrive archive. Deleting anything else needs Matt's OK.
- **Report outcomes plainly.** When a check fails, investigate before relaxing it. Phase 1 examples:
  - Ridership "duplicates" turned out to be unassigned ridership.
  - Orphan routes turned out to be routes retired in 2017.

## Environment gotchas (Windows dev PC)

- `uv` lives in `%APPDATA%\Python\Python313\Scripts` and `pn` in `%USERPROFILE%\.local\bin`. Both are on the user PATH, but tool shells may need:
  ```bash
  export PATH="/c/Users/Matt/AppData/Roaming/Python/Python313/Scripts:/c/Users/Matt/.local/bin:$PATH"
  ```
- **Long bash heredocs** containing quotes failed in the Claude Code Bash tool. Write scripts or YAML with the file-writing tool instead.
- **The Windows console is cp1252.** The CLI reconfigures stdout to UTF-8. Set `PYTHONIOENCODING=utf-8` for ad-hoc Python.
- **`*` arguments** get expanded into filenames by the Windows launcher. `pn check` with no arguments means all datasets.
- **Pin `duckdb>=1.5.6,<2`.** DuckDB 2.0 is due around late October 2026; don't upgrade until 2.0.x patches land.
- **ArcGIS layer metadata is volatile** (renderer colours change per request). Connectors write it as `_layer.json`, and `_`-prefixed files are excluded from change detection.
