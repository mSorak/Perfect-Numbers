# 03 — Proposal: a central data hub for Perfect Numbers

Status: **v3: Matt's answers incorporated** (`answers.md`, 2026-10-13); v2 was revised after an independent review pass · Author: Claude (acting as senior data engineer)

Reads with:
- `01_investigation.md`: the evidence, with requirement IDs R1–R15 and issues #1–#9.
- `02_source_landscape.md`: how to get each source.
- `04_questions.md` and `answers.md`: the questions and Matt's answers (summarized in §0.2).
- `appendix_dataset_register.csv` and `examples/`.

---

## 0. Summary

**What changes day to day**
- Shared data lives in one place on the dev PC, outside OneDrive. The repo itself is remade **pipeline-first**: the data hub's code, catalog and docs are the repo; piece-specific work lives in `projects/<slug>/` only when needed (§3.1).
- A project asks for a dataset by name (`crash.report_cost`, `geo.tract`, `census.acs5`) and gets the current, documented version. Nothing gets copied between projects again.
- Refreshing a dataset is one command. Checks run automatically, and everything downstream rebuilds.
- When a post goes out, one command freezes the exact data behind it.
- The source behind a dataset can change without breaking anything that uses it. Today's half-year MDSP exports could become an automated monthly pull, for example.

**What it fixes.** The investigation found 9 verified data-integrity issues, about 14 GB of duplicated or unnecessary files, three copies of the crash app, and datasets whose meaning silently drifted (AADT "current" year, undated Zillow files). Each issue maps to a specific safeguard here: automatic checks, shared definitions, or publish-time review.

**What it costs**
- **$0.** No cloud for now (B3). Backups are a one-way copy into your existing OneDrive.
- **Your time, rough estimates.** Housekeeping ≈ 4–6 hours. The first working slice (crash + geography, reproducing the crash app's numbers exactly) ≈ 25–35 agent-assisted hours, of which perhaps 8–12 are yours (reviewing, deciding, downloading). After that, roughly 2–6 hours per dataset as your next pieces need them, and ≈ 1–2 hours a month of upkeep.

**What's deliberately deferred.** Cloud storage, Claude skills, DuckLake, the politics/elections backbone (no election content planned), and every dataset no upcoming piece needs.

### 0.2 Decisions recorded (2026-10-13, from `answers.md`)

| Topic | Decision | Effect on the plan |
|---|---|---|
| Next pieces (A1) | 1) **Baltimore street-design authority / bus-lane priority corridors** (in progress). 2) **JFX / I-83, ReVision Zero #3** (crashes, costs, AADT). 3) Later: traffic violence × crime. No election content; baseball/math out of scope. | Roadmap reordered: foundation → **bus-corridor slice** → **I-83 / crash slice** (includes the crash parity test) → backlog (§10). Politics domain deferred. |
| Time budget (A5) | Not answered | Keep the default assumption: ~4–6 h/week of your time during setup, 1–2 h/month after. Tell me if that's off. |
| Machines and storage (B1–B3) | Writing on the laptop; data and dev work on **this PC**, which can stay on. Repo can leave OneDrive. **No cloud for now.** | Data root and dev repo live on the PC; scheduled refreshes via Task Scheduler are feasible once a source is automated. The laptop needs only the repo (code + docs) and published packs. |
| Repo (C1–C3) | **Remake the repo pipeline-first.** The data pipeline is the public, useful part; blog text isn't needed. Piece work goes in subfolders only when needed. Separate projects (crash costs app) keep their own repos. | New repo layout (§3.1) and a non-destructive migration (§10 Phase 0). The unpushed `3d29916` commit becomes moot: the old repo stays in OneDrive as an archive and is never pushed. |
| Tooling (D1–D4) | Cards + small SQL runner; agents write only via `pn`; all Claude tools, Cursor possibly, local models long-term; float → pin → pack. | `AGENTS.md` stays canonical (Cursor reads it). Read-only DuckDB MCP server moves up (useful in Claude Desktop). Keep generated docs compact so local models can use them. |
| MDSP crash data (E1) | Recipe confirmed. **All tables and all variables.** Automation wanted — **prefer an API route over Playwright.** The "Data" download is sometimes greyed out, possibly related to record counts. No bulk-access request for now. | Intake covers every tab. A time-boxed **API investigation spike** comes before any Playwright work. Exports use smaller windows (monthly, falling back to weekly) to sidestep the record-count issue. |
| Methodology, other datasets, documents, field data (E2–E5) | No cost-method change; nothing new requested; document library yes; field data stays in projects. | Method 2026.1 stays; the KABCO variant is dropped from the plan. |
| Publishing, integrity, secrets (F, G) | Defaults accepted. | Packs, pins, chart registry, correction alerts, raw retention, one key file, rotate the IPUMS key. |

### 0.1 Stack at a glance

| Layer | Choice |
|---|---|
| Storage | Parquet / GeoParquet files in `raw → staging → marts` folders under one data root (`PN_DATA_ROOT`) |
| Query | DuckDB 1.5.x. Every session loads a generated `catalog.sql` that defines one view per dataset, with column descriptions. |
| Acquisition | A small Python package, `pndata`, with about 10 connectors. Each writes immutable raw snapshots plus a manifest (URL, time, hash). |
| Access modes | Mirror, cache-through, live and manual for sources; derived for computed datasets (§3.4) |
| Documentation | One YAML **dataset card** per dataset is the source of truth. Human and agent docs are generated from the cards; `AGENTS.md` sets the rules. |
| Transforms | SQL files (Python where needed), run in dependency order by `pn build`. dbt-duckdb is the upgrade path (§6.6). |
| Quality | Checks at intake and at build; a shared metric library; a publish-time review |
| Integrity | Immutable raw snapshots, versioned builds, project pins, and a frozen **data pack** per post |
| Interface | One CLI, `pn`, installed with `uv` |

A glossary is at the end of this document.

---

## 1. Goals and non-goals

**Goals**
1. **Find once, reuse everywhere.** Any project can query cleaned, documented data in a line or two without knowing where it came from (R1, R2).
2. **Updates are routine.** New crash months, a new ACS vintage or this month's MTA ridership is one command with automatic checks (R3, R8).
3. **Sources can change underneath.** Moving from manual exports to an API changes a connector and a staging query, not the projects that use the data (R2).
4. **Integrity a journalist can stand behind.** Every number traces back to a source URL, a retrieval time, a file hash and a code version. Whatever was published is frozen (R3, R11).
5. **Legible to AI agents.** An agent can discover datasets, understand grain, keys and caveats, write correct queries, and add datasets by following written standards (R10).
6. **Solo-sized.** Local, Windows-native, no servers, mostly files. Every piece can be replaced (R13).

**Non-goals (for now)**
- Multi-user concurrency, streaming, or an orchestration server.
- Managing photos, video or drafts.
- Rewriting published analyses. Those migrate only when you next touch them, apart from the parity test in §10.

---

## 2. Design drivers

**D1 — Reference, don't copy.** Copying caused stale data and broken lineage: the Baltimore transfer, the FARS copy into us29, and the 2.9 GB stale copy in `source/` that still contains the bad vehicle file. The hub is the only home for shared data.

**D2 — Separate *what* from *how*.** A dataset's contract (ID, grain, keys, columns, meaning) is independent of how it's acquired. Projects bind to the contract.

**D3 — Append-only evidence; everything else is rebuildable.** Four layers are append-only and get backed up: raw snapshots, API cache, documents, and data packs. Staging and marts are rebuilt from them, using code at a git SHA and the snapshot list recorded in the committed manifest.

**D4 — Store what you use, at the scope you use.** Fetch Maryland/DMV data, not national shapes. Fetch the ACS tables you query, not entire products. Mirror a source only when it is fragile, revised, rolling or slow. Add a dataset when a piece needs it.

**D5 — Make time explicit.** Every table carries:
- *vintage*: which edition of the data it is;
- *period*: what time the rows describe.

Both are named columns, so a "current" column like AADT's can't slip through. That property is explicit and tested.

**D6 — One geography backbone, one entity backbone.** Census geographies, ID crosswalks, point-in-polygon assignment and custom-area aggregation are solved once. The same goes for people, offices, districts, contests and bills.

**D7 — Documentation is data.** Cards are structured YAML, checked against the real tables. Human and agent docs are generated from them. Hand-written prose is kept for judgment: methodology, decisions and caveats.

**D8 — Fail loudly at the boundary.** Checks run when data enters the hub and again when it is built. A bad export stops the build; it doesn't flow into a chart.

**D9 — Boring and portable.** Files, SQL, Python and YAML. Because the data is Parquet, any component can be swapped without migrating data.

---

## 3. Architecture

### 3.1 Two homes: the repo and the data root

**Git repo: remade pipeline-first** (decision C, 2026-10-13). It lives on the dev PC outside OneDrive (e.g. `C:\Users\Matt\code\perfect-numbers`) and publishes to GitHub (`mSorak/Perfect-Numbers`). The hub *is* the repo: no `data/` sub-folder.

```
perfect-numbers/
├── README.md                     ← what the pipeline is, how to use it (public face)
├── AGENTS.md, CLAUDE.md (@AGENTS.md)
├── pyproject.toml, uv.lock       (pndata + pn)
├── src/pndata/                   connectors, runner, checks, geo, metrics, cli
├── catalog/
│   ├── datasets/<domain>/<dataset>.yml   ← dataset cards (source of truth)
│   ├── sources/<source_id>.yml (+ .md)   ← source cards (publisher, access recipe, terms, cadence)
│   ├── seeds/*.csv                       ← small reference tables (unit costs, code maps)
│   ├── manifests/raw_manifest.jsonl      ← one line per raw file (committed)
│   ├── metrics.sql + metrics.md          ← standard metric macros + definitions
│   ├── conventions.md
│   └── generated/                        ← CATALOG.md, datasets/*.md, STATUS.md, CHANGELOG.md
├── pipelines/<domain>/<dataset>.sql|.py  ← build logic referenced by cards
├── queries/examples/*.sql                ← question-first example queries
├── docs/design/ (this folder), docs/decisions/ (short ADRs)
└── projects/<slug>/                      ← only when a piece needs code worth keeping
    ├── project.yml                       ← datasets used, pins, outputs
    └── notebooks / scripts / README
```

**What stays out of the new repo.** Blog text, photos, drafts and the 2024–2026 project folders stay in the current OneDrive folder, which becomes a read-only archive; nothing is deleted. The crash-cost app keeps its own repo (`mSorak/md_crash_costs`) and reads hub marts via `pn export`. Old GitHub history is preserved under a tag or branch (§10 Phase 0).

**Data root** (`PN_DATA_ROOT`, on the dev PC, outside OneDrive and git; default `C:\Users\Matt\pn-data\`). Append-only layers are backed up; regenerable layers are not. The laptop doesn't need a data root: it uses the repo plus published packs.

```
C:\Users\Matt\pn-data\
├── inbox\                          ← manual downloads land here
├── raw\<source>\<entity>\<snapshot_id>\        ← append-only, read-only files (backed up)
├── cache\api\<connector>\<request_hash>.parquet ← append-only (backed up)
├── docs\<doc_id>\original.*, text.md           ← append-only (backed up)
├── packs\<date>_<post_slug>\                   ← append-only (backed up)
├── staging\<domain>\<dataset>\build=<id>.parquet ← rebuildable; last N builds kept
├── marts\<domain>\<dataset>\build=<id>.parquet   ← rebuildable; last N builds + pinned kept
├── catalog.sql                     ← generated: views + comments + macros
└── tmp\                            ← DuckDB spill
```

**Why the data root sits outside OneDrive:**
- DuckDB writes WAL and temp files next to the files it uses.
- Sync clients lock and re-upload files mid-write.
- Files-On-Demand can silently turn local files back into cloud placeholders.

I found no DuckDB-specific corruption report for OneDrive. The adjacent evidence points the same way: WAL-replay failures after interrupted writes, sync churn on database files, and git repositories corrupted inside OneDrive. The repo also moves out of OneDrive (decided), with GitHub as its backup.

**Backup.** One-way, never-deleting copies of the four append-only layers: `robocopy` *without* `/MIR` to a OneDrive archive folder, run nightly by Task Scheduler (the PC stays on). No cloud bucket for now. `pn intake` marks raw files read-only (`attrib +R`), and `pn status` re-verifies a sample of hashes.

**Re-acquisition.** If the data root is lost, every non-manual source can be re-fetched from the committed manifest. But sources that revise or overwrite in place (AADT, Zillow, GTFS, SBE, MTA Power BI, WMATA) will return *different bytes*. The backup is the only exact copy.

### 3.2 Layers

| Layer | Holds | Written by | Mutability |
|---|---|---|---|
| `inbox/` | Manual downloads awaiting intake | you | transient |
| `raw/` | Exactly what the source served, one folder per retrieval. Path is `raw/<source>/<entity>/<snapshot_id>/`, where `snapshot_id` is UTC `YYYYMMDDTHHMMZ`, plus `__<period>` for batch sources (e.g. `20260606T1829Z__2025H2`) | `pn fetch` / `pn intake` | append-only, files read-only |
| `cache/api/` | Responses from cache-through API calls, keyed by request hash, with manifest lines | connectors | append-only (expiry per card) |
| `docs/` | Document library: original file, extracted text, metadata | `pn intake --doc` | append-only |
| `staging/` | One clean table per source entity: typed, snake_case, canonical keys, explicit vintage and period, snapshot-selection rule applied | `pn build` | versioned builds |
| `marts/` | Joined and derived products: costs, summaries, exposure, crosswalks, entity tables | `pn build` | versioned builds |
| `packs/` | Frozen inputs and outputs per published piece | `pn pack` | append-only |

**Consumers see datasets, not layers.** `crash.acrs_report` is a view onto the *current* build, whichever layer that build lives in. Builds are kept (default: the last 5, plus any build referenced by a project pin or pack), so pinning and "as of" queries work without DuckLake.

### 3.3 Domains and dataset IDs

The ID `<domain>.<dataset>` is the view name in DuckDB, the card path, and the docs page.

| Domain | First datasets (§9 has the full plan) |
|---|---|
| `geo` | `geo.county`, `geo.tract`, `geo.block_group`, `geo.place`, `*_display` (simplified, map-only), `geo.md_leg_district`, `geo.council_district`, `geo.custom_area`, `geo.xwalk_tract_2010_2020` |
| `census` | `census.acs5` (long format: geo × vintage × variable, with MOE), `census.acs_variable`, `census.dec2020_dhc`, `census.pep_*`, `census.bps` |
| `crash` | `crash.acrs_report`, `crash.acrs_vehicle`, `crash.acrs_person`, `crash.acrs_report_removed`, `crash.report_geo`, `crash.report_cost`, `crash.summary_*`, `crash.fars_*`, `crash.moco_incident` |
| `traffic` | `traffic.aadt_segment` (long format: segment × year), `traffic.aadt_station`, `traffic.street_segment` (Baltimore City centerline), `traffic.road_jurisdiction` (who maintains/controls each road: SHA vs city vs county) |
| `transit` | `transit.mta_ridership_*`, `transit.ntd_monthly`, `transit.gtfs_*`, `transit.stop_ridership`, `transit.bus_segment_service` (street segment × time band: trips, routes, riders), `transit.station`, `transit.route_xwalk` |
| `housing` / `econ` | `housing.zhvi`, `econ.cpi_u`, `econ.laus_county`, `econ.fred_observation` |
| `crime` | `crime.baltimore_nibrs` |
| `pol` / `leg` | `pol.person`, `pol.person_xref`, `pol.name_alias`, `pol.office`, `pol.office_term`, `pol.election`, `pol.contest`, `pol.candidacy`, `pol.result`; `leg.bill`, `leg.bill_sponsor`, `leg.committee`, `leg.committee_membership` |
| `ref` | Seeds: `ref.county_codes` (FIPS ↔ MDOT ↔ SBE ↔ names), `ref.acrs_severity`, `ref.acrs_injury_to_mais`, `ref.nhtsa_unit_cost_2019`, `ref.fars_codes`, `ref.party` |
| `docs` / `pub` | `docs.document`; `pub.post`, `pub.chart`, `pub.pack` |

### 3.4 Access modes: when to store, when to call an API

Every dataset card declares one mode:

| Mode | Meaning | Use when | Examples |
|---|---|---|---|
| **mirror** | Pull the dataset at your scope on a cadence; keep the snapshots | The source is **revised** (crash reports, LAUS, Zillow), **rolling** (AADT drops old years), **fragile** (dashboards, scraped HTML, the Power BI endpoint) or **slow/large** (FARS) | ACRS, AADT, FARS, MoCo crashes, NIBRS, Zillow, LAUS, MTA ridership, SBE, MGA bills, GTFS |
| **cache-through** | Call the API the first time a slice is requested, keep the response with its manifest, and serve from disk afterwards. Optional expiry (TTL) in the card. | A **large, stable, versioned** API where you only ever use small slices | Census ACS/decennial (by table × geography × vintage), IPUMS, CPI-U NSA (never revised), HUD |
| **live** | Query directly, with only an HTTP cache | **Exploration only.** `pn.live.get()` logs URL, parameters and time to a session log. Anything used in a draft is promoted with `pn promote` to cache-through or mirror, so it gets a manifest. | Ad-hoc Socrata, Census or FRED queries |
| **manual** | You download; `pn intake` moves the file to raw, hashes it, records how it was obtained, and checks it | **No programmatic route** | MDSP exports (until automated), JCHS, PDFs, voter-registration PDFs |
| **derived** | Built by the hub from other datasets | Every staging or mart product | `crash.report_cost`, `crash.summary_county`, `geo.custom_area` |

**Should data be stored at all?** A pure "call the API every time" approach is right for exploration and wrong for publishing:
- Sources revise and disappear.
- Several key sources have no API.
- You need to reproduce what you published.

Cache-through is the middle path. You don't hoard all of ACS, but every slice you used is kept with its provenance. Given the Commerce order (DAO 216-26) that has delayed ACS releases and may coarsen future ones, that is also insurance.

### 3.5 The query layer

`pn catalog` writes **`catalog.sql`**. It holds `CREATE VIEW` statements pointing at each dataset's current build (absolute paths), `COMMENT ON` for every view and column, and the metric macros. Every reader loads it into an **in-memory** DuckDB:
- `pn.connect()`;
- `duckdb -init "C:\Users\Matt\pn-data\catalog.sql"`;
- later, the MCP server's `--init-sql`.

No reader ever holds a database file open, so builds and catalog regeneration never collide with an open notebook. (On Windows, a DuckDB file held read-only by one process blocks writers and replacement; the independent review reproduced this.)

**Python API**

```python
import pndata as pn
con = pn.connect()                         # in-memory DuckDB + catalog.sql + spatial
con.sql("from crash.report_cost where year = 2025 and county_geoid = '24027'").df()
df  = pn.read("crash.summary_county", where="year = 2025")          # → DataFrame
gdf = pn.read_geo("geo.tract", vintage=2024, where="county_geoid = '24031'")  # → GeoDataFrame
acs = pn.census.acs5("B25034", geo="tract", state="24", county="031", vintage=2024)  # cache-through
pn.describe("crash.report_cost")           # prints the card
con = pn.connect(project="2026/crash_costs")  # honours the project's pins (§5.1)
```

**Apps.** `pn export app:crash-cost-md` writes the app's `data_cache/` from marts and adds a `meta.json` recording build IDs. `pn status` lists apps whose exported data is older than the current marts. Redeploying stays manual.

### 3.6 The geography backbone (D6)

**Boundaries:**
- **Tract, block group and place**: TIGER/Line *per-state* files for MD, DC and VA, one set per vintage.
- **County and ZCTA**: national-only from the Census Bureau. Download once per vintage, filter to MD/DC/VA at intake, and record the national file's URL and hash.
- **Districts**: Maryland iMAP layers for 2022 legislative and congressional districts and 2026 precincts; county sources for council districts.

**Display vs analysis geometry.** Analytical geometry is full resolution. Simplified display layers carry a `*_display` suffix, never feed analysis, and come at first from the crash app's existing files.

**Canonical key.** `geoid`, stored as zero-padded text, plus `geoid_vintage`. One macro and seed handle the other ID formats (`GISJOIN`, `1400000US…`, `STATEA+COUNTYA+TRACTA`), replacing today's three converters.

**Point assignment.** `pn.geo.assign(points, levels=[...], vintage=2024)` runs once per point dataset (crashes, crime), so every project uses the same assignment.

**Custom areas.** `geo.custom_area` stores named areas (the ESS plan area, station catchments, corridor buffers) as a polygon or a member list, with apportionment weights. `pn.census.aggregate(area_id, table)`:
- sums counts;
- combines MOEs by root-sum-of-squares;
- estimates medians from distribution tables, instead of population-weighting tract medians.

**CRS policy:**
- Store as **OGC:CRS84** (lon/lat, the GeoParquet default). NAD83 sources are relabelled, not transformed; the shift is under 2 m.
- Measure in **EPSG:26985** (NAD83 / Maryland, metres) within MD/DC/Northern Virginia, and **EPSG:5070** for national work.
- Take land area from the Census **Gazetteer `ALAND`**, not from polygons.
- **Geometry check:** per tract, polygon area in EPSG:26985 ÷ (ALAND + AWATER) must lie in [0.99, 1.01]. Cartographic (shoreline-clipped) files are compared with ALAND within 5% instead. This catches unit errors like BVA's, without failing on water.
- **Phase 1 spike:** confirm what DuckDB 1.5 writes for geometry in Parquet (GeoParquet 1.1 metadata or the native type), and pin the writer.

### 3.7 The entity backbone for politics (D6)

This adopts the schema already designed in `2026/mta_overview/data-acquisition-plan.md`.

**Tables:**
- `pol.person` (an internal `person_id`).
- `pol.person_xref`: Open States ID, MGA slug with valid-from/to dates, MSA ID, SBE committee name, LegiScan ID.
- `pol.name_alias`.
- `pol.office` and `pol.office_term`.
- Districts keyed by `(plan_id, district_code)`.
- `pol.election`, `pol.contest`, `pol.candidacy`, `pol.result`.
- `leg.bill` keyed `(session, bill_number)`, with resolved sponsors.

**Rule:** no positional or name keys survive staging. Unresolved names are reported, not dropped.

### 3.8 The document library (R14)

`pn intake --doc` stores:
- the original file;
- its SHA-256 and source URL;
- publisher, date and title;
- extracted text, with OCR on request.

Anything an LLM extracts from documents (questionnaire answers, summaries) is stored with the prompt, the input document hashes, the model name and the output.

---

## 4. Catalog and documentation

### 4.1 One source of truth, generated views of it

| Artifact | Written by | Content |
|---|---|---|
| `catalog/sources/<source>.yml` (+ `.md`) | hand (agent-assisted) | Publisher, landing page, access recipe (exact clicks for manual sources; endpoint and parameters for APIs), auth, **cadence** (only here), terms and citation, hazards |
| `catalog/datasets/<domain>/<dataset>.yml` | hand; **checked against data** | The dataset card (§4.2) |
| `catalog/metrics.sql` + `metrics.md` | hand | Metric macros and their definitions (§7.3); Python calls the same SQL |
| `2026/<project>/project.yml` | hand | **The only hand-written record of who uses what.** Card `used_by` lists and `pub.*` are generated from it. |
| `catalog/generated/CATALOG.md` + `datasets/<id>.md` | `pn catalog` | Index and one page per dataset: card plus live stats (rows, coverage, last refresh, snapshots, lineage up and down) |
| `COMMENT ON` in `catalog.sql` | `pn catalog` | Table and column descriptions visible to any SQL client |
| `catalog/generated/STATUS.md`, `CHANGELOG.md` | `pn status` / builds (+ notes) | Freshness and stale consumers; dataset-level change log |
| `queries/examples/*.sql` | hand | Question-first examples, the most useful few-shot material for text-to-SQL |
| `admin/decisions/NNNN-*.md` | hand | Short decision records |

**Anti-drift rule.** `pn check`:
- **errors** on any undocumented or missing column in a **mart**;
- only **warns** for staging, because wide sources like FARS have hundreds of columns.

Staging selects only the columns that are used; everything else stays available in raw. A description may point to the source manual, for example "see acrsfieldreference.pdf p. 12".

### 4.2 The dataset card

A worked example is in `examples/dataset_card_example.yml`. Required fields:
- `id`, `title`, `description`, `grain`, `primary_key`.
- `access_mode`, `source` (source ID; not needed for derived datasets).
- `build`: `sql:` / `python:` / `seed:` / `connector:`, plus `depends_on`.
- **`vintage` and `period` semantics, and the snapshot-selection rule** (§5.2).
- `coverage`, generated.
- `columns`: name, type, description, units, and a `pii` tag where applicable. Coded values point to `ref.*` tables.
- `tests`.
- `license`, `redistribution` (allowed / attribution / not allowed), `citation`.
- `caveats`, dated, with evidence links.
- `example_queries`.

Sensitivity is set **per column** (`pii: true`); the dataset- and source-level flags are derived from it.

### 4.3 Instructions for AI agents (kept lean)

- **`AGENTS.md`** at the repo root is the canonical file; a draft is in `examples/AGENTS.md`. It covers where things are, the five rules, the commands, and how to find and add data. Codex, Cursor, Copilot and others read it natively.
- **`CLAUDE.md`** contains the single line `@AGENTS.md`. Claude Code reads `AGENTS.md` directly only when no `CLAUDE.md` exists, so an import is the reliable route.
- **Generated docs plus SQL comments** are the core. Keep each dataset page short: local models (a long-term interest) have small context windows.
- **Read-only DuckDB MCP server** (`mcp-server-motherduck`, local, read-only, `--init-sql` loading `catalog.sql`) comes in during the foundation phase, since you use Claude Desktop as well as Claude Code. Cursor can use the same server.
- **Deferred:** Claude skills (start with one, `pn-add-dataset`, after the intake standard has been used twice); `llms.txt`.

---

## 5. Workflows

### 5.1 Using data in a project: float, pin, freeze

1. **Declare.** List the datasets you use in `project.yml` (example in `examples/project_example.yml`). Globs such as `geo.*_display` are allowed.
2. **Explore (float).** `pn.connect(project=...)` gives current builds. A refresh can change your numbers, and that's expected while exploring.
3. **Draft (pin).** `pn pin 2026/<project>` records the current build ID of each declared dataset in `project.yml`. Re-running the notebook now gives the same numbers until you deliberately run `pn pin --update` and review `pn diff`.
4. **Publish (freeze).** Build a data pack (§5.4).
5. **Reusable derived tables become hub marts**, with cards. A Baltimore tract panel, for example, lives in the hub, not as a parquet file inside the project.

### 5.2 Refreshing a dataset

```
pn status                         # what's due (cadence from source cards), stale consumers, unverified pins
pn fetch mdot_sha_aadt            # API source;  or: drop files in inbox → pn intake mdsp_acrs --period 2026H1
pn build crash.report_cost --upstream --downstream   # rebuild what changed + dependents; run tests
pn catalog                        # regenerate catalog.sql + docs + changelog entry
pn export app:crash-cost-md       # if an app consumes it
```

**Intake checks run before anything is promoted.** If a check fails, the snapshot is quarantined and `pn status` says why. Checks:
- the header signature;
- row counts against the previous snapshot for the same period;
- entity ratios (vehicles per report);
- date coverage;
- coordinate bounding box;
- for MDSP, **independent reconciliation** with the dashboard's anonymous `.csv` count endpoint. It returns county × severity distinct-report counts for any window; H1-2025 agreed with your file within 0.08%.

**Snapshot selection for revised sources (crash data).**
- For each crash period, take **all entities from the most recent complete snapshot** covering that period.
- A report that disappears from the newest snapshot is dropped and logged in `crash.acrs_report_removed` (report number, last snapshot seen).
- If a revised crash date moves a report between periods, deduplicate on report number, latest retrieval first.

This stops withdrawn reports from lingering, and stops reports and vehicles from different export sessions being mixed (issue #9). `pn diff crash.acrs_report` lists reports added, removed or modified between snapshots.

**Reproducible rebuilds.** Staging picks snapshots from the **committed** `raw_manifest.jsonl`, not by scanning the folder. `pn build --as-of <date>` rebuilds a past state. Each `_build.json` records:
- input snapshot IDs and hashes;
- the git SHA;
- the `uv.lock` hash;
- DuckDB and tool versions;
- settings such as `geometry_always_xy`.

Unattended refreshes commit the manifest, or `pn status` warns.

### 5.3 Adding a new dataset: the intake standard

`pn new <domain>.<dataset>` scaffolds the files. Whoever adds the dataset, you or an agent, works through:

1. **Source card.** Prefer, in order:
   1. a documented API or bulk file;
   2. a stable file URL;
   3. an ArcGIS or Socrata endpoint;
   4. scraping, with the raw HTML saved;
   5. manual intake.
2. **Access mode**, with a one-line justification (§3.4).
3. **Scope.** MD/DMV unless the analysis needs more.
   - National-only files under ~200 MB are kept as served.
   - Larger ones are kept as the subset you need, with the original's URL, size and hash in the manifest.
4. **Acquire** to `raw/` with a manifest line:
   - URL and final URL, HTTP status, content type;
   - parameters (with credentials redacted, because the manifest is committed);
   - `retrieved_at` (UTC);
   - SHA-256, bytes, rows, ETag / Last-Modified;
   - fetch-code git SHA and original filename;
   - for manual intake, how the retrieval time was established and which UI settings were used.

   A snapshot whose hash hasn't changed is skipped.
5. **Stage.**
   - snake_case columns; canonical keys (`geoid`, `report_number`, `person_id`); explicit `vintage` / `period`;
   - codes kept *and* labelled through `ref.*`;
   - sentinel values turned into NULL;
   - no renames that lose meaning (keep FRED/BLS series IDs, for example).
6. **Card** with every mart column documented.
7. **Tests.** At minimum:
   - primary key unique and not null;
   - relationships to parent tables;
   - accepted values for coded fields;
   - one **domain sanity check** that would catch a plausible failure (a ratio, a published total, an area check, a row-count band).
8. **Link** to the geography and entity backbones.
9. **Example query** in `queries/examples/`.
10. **Changelog line** saying why the dataset was added.

**Definition of done:** `pn check <id>` passes, the dataset appears in `CATALOG.md`, and an agent with no other context can answer a question with it.

### 5.4 Publishing a piece

1. **In the notebook, register each output.** For example `pn.publish(df, name="us29_rates", chart="Mv21f")` for every number or chart that will appear in the post.
2. **`pn pack <post_slug> --project 2026/<project>`** freezes into `packs/<date>_<slug>/`:
   - the registered outputs (Parquet + CSV);
   - the pinned input build IDs and hashes;
   - the git SHA;
   - a README with sources and citations generated from the cards.

   A chart that has no registered output fails the pack.
3. **Register Datawrapper charts** (ID, version, uploaded CSV) in `pub.chart`.
4. **Publish review.** An agent checklist (a skill, later) compares every rate label against `metrics.md`:
   - do numerator and denominator cover the same window?
   - is the unit right?
   - are seasonally adjusted and unadjusted series mixed?
   - which chart *version* is embedded?

   Labels are still typed by hand in Datawrapper, so this review is the safeguard, not a guarantee.
5. **Public data.** Optionally publish the pack: committed to the repo if under ~50 MB and licence-cleared, attached to a GitHub release, or on Hugging Face. This keeps the repo README's promise of "code, data … for each post" while raw data stays out of git.

### 5.5 Changing how a dataset is acquired

1. Add a source card and connector for the new route.
2. Write a staging query that maps it to the **same** canonical columns, with a `source_system` column during the overlap.
3. Run a **parity test** on the overlap period.
4. Switch the card and record the change in the changelog.

Projects change nothing (D2).

### 5.6 Working with AI agents

- **Read freely.** Agents read freely.
- **Write through `pn` only.** It writes manifests and runs the checks. Agents never edit `raw/` (files are read-only, and hashes are verified). They never `--force` past a failed check without your explicit OK.
- **Credentials.** Keys live in `%USERPROFILE%\.config\pn\.env` and are never printed or committed. Rotate the IPUMS key.
- **One caveat.** A "read-only" DuckDB session can still write files with `COPY … TO`. Immutability therefore comes from file attributes and hash checks, not from connection mode.

---

## 6. Technology choices and alternatives

### 6.1 Storage format: Parquet / GeoParquet 1.1 (zstd)
- **Why:** every tool you use reads it: DuckDB, pandas/geopandas, polars, DuckDB-WASM, R2, Hugging Face. FARS shrinks from ~8.4 GB of CSV to roughly 1 GB.
- **Not yet:** GeoParquet 2.0 is still a release candidate. Revisit when it's final and geopandas, GDAL and DuckDB agree.
- **Alternatives:**
  - one large `.duckdb` file: single writer, opaque, and its storage format changes in DuckDB 2.0;
  - GeoPackage/SQLite: row-oriented, so slow for analytics.

### 6.2 Engine: DuckDB 1.5.x
- **Why:** geometry is a core type as of 1.5. It reads remote HTTP/R2 files, Excel and GDAL formats, and it already powers your app.
- **Versions:**
  - Upgrade from 1.1.2.
  - Pin `duckdb>=1.5.6,<2`. DuckDB 2.0 is tentatively due around 2026-10-21; move after its first patch releases.
  - Set `geometry_always_xy = true` now.
  - `pn.connect()` asserts the version.
- **Alternatives:** Postgres/PostGIS (a server to run); polars (a DataFrame library, not a catalog).

### 6.3 Location: outside OneDrive (§3.1)
The alternative is to keep everything in OneDrive, with files set to "Always keep on this device" and no live database files. That's workable for Parquet but fragile. **Your answer to B1 decides this.**

### 6.4 Versioning: append-only evidence + versioned builds + pins + packs
- **Why this is enough:**
  - Raw snapshots are versioned by construction.
  - Builds are kept, so pins and `--as-of` work.
  - Packs freeze what was published.
  - Packs are *better* than time travel for published numbers, because they store the exact outputs.
- **Upgrade path: DuckLake.** v1.0 shipped April 2026 and is described as production-ready. It adds snapshots, time travel and transactions over Parquet. It mainly helps pinning before publication and multi-machine use. Reconsider after DuckLake 1.1 settles, around early 2027.
- **Alternatives:** DVC (now under lakeFS; for teams); Git LFS (10 GB quota, poor with churn); Iceberg/Delta (cluster-scale).

### 6.5 Ingestion: about 10 small connectors in `pndata`

| Connector | Covers | Phase |
|---|---|---|
| `manual` | Inbox intake (MDSP, JCHS, PDFs) | 1 |
| `http_file` | FARS, TIGER, Gazetteer, Zillow, PEP, BPS, SBE CSVs, MGA JSON, GTFS | 1 |
| `census_api` | ACS / decennial / PDB, cache-through; key required | 1 |
| `rest_json` | BLS (CPI, LAUS), FRED, HUD, FBI CDE, FEC, LegiScan | 1 (BLS for the crash slice in Phase 2) |
| `arcgis` | AADT, iMAP, Baltimore NIBRS, BaCo crashes (paged `resultOffset`, or GDAL ESRIJSON); also Baltimore street centerline and SHA jurisdiction | 1 |
| `socrata` | MoCo, MD, NTD (SODA 2.1 + app token) | 1 (NTD) |
| `ipums` | One NHGIS client merging purple_line's hash cache with BVA's extract-definition/manifest pattern (`IPUMS_API_KEY`); needed for crosswalks and time series | 3 |
| `tableau_public` | `.csv` view endpoints (MDSP reconciliation, WMATA entries); MDSP row-level export via an API route if the Phase 2 spike finds one, otherwise Playwright | 2 |
| `powerbi_public` | Your MTA `querydata` + DSR decoder, with a schema-drift check | 1 |
| `html_snapshot` | Save raw pages, then parse them (Maryland Manual, committee pages) | 3 (if politics returns) |

These build on code you already have: `src/aadt.py`, `nhgis_client.py`, `scrape_mta.py`, `download_questionnaires.py`.

**Alternative: dlt 1.31.** It offers declarative REST sources, incremental cursors and a DuckLake destination, but no maintained Socrata or ArcGIS source we could verify, and no DuckDB geometry. Worth it if you add several paginated JSON APIs with incremental sync.

### 6.6 Transformation: plain SQL runner first; dbt-duckdb as the upgrade path

**Recommendation: `pn build`.** It is a few hundred lines in `pndata`:
- reads `depends_on` from the cards;
- runs each step's SQL (or Python function) in a private in-memory DuckDB, with its inputs attached as views;
- writes Parquet with `COPY`;
- runs the card's tests;
- promotes the build.

Seeds are CSVs converted to Parquet. Spatial work uses DuckDB spatial SQL; geopandas is used only where it's clearly easier.

**Why not dbt-first (the first draft recommended it):**
- **The catalog has to cover more than transforms.** It must also describe raw sources, cache-through datasets and documents, so a tool-neutral card is needed regardless.
- **Plumbing issues on Windows:**
  - dbt's target-database file collides with readers;
  - seeds become tables rather than Parquet;
  - schema names need an override macro;
  - model names must be globally unique (`crash.moco_incident` vs `crime.moco_incident`);
  - Jinja is needed for every output location;
  - test syntax has changed across versions.
- **The dbt ecosystem is mid-transition.** dbt Labs merged with Fivetran in June 2026, and the Rust-based v2 line can't yet load DuckDB's spatial extension without a workaround.

**Upgrade path.** Cards map one-to-one onto dbt `schema.yml` (descriptions, columns, tests), and the SQL is plain DuckDB. A generator can emit a dbt-duckdb project mechanically. Upgrade when there are many multi-step models, or when you want dbt's lineage UI and its MCP server.

**Alternatives:** SQLMesh (now a Linux Foundation project); Hamilton/Kedro (Python-first).

**Minimum viable fallback.** If even this feels heavy: Parquet + views + YAML cards + three scripts (intake, build, catalog). That is the same layout without the CLI conveniences.

*This choice is question D1 in `04`.*

### 6.7 Validation
- **Card-declared tests**, executed by `pn check`: `unique`, `not_null`, `accepted_values`, `relationships`, and SQL assertions with thresholds.
- Intake checks.
- Pandera only at Python boundaries.
- **Not:** Great Expectations (heavy) or Soda Core (moved to the Elastic License, with syntax churn).

### 6.8 Orchestration
- The `pn` CLI, built with typer, installed once with `uv tool install --editable .` from the repo root, so `pn` is on PATH everywhere.
- Windows Task Scheduler on the dev PC (it stays on) runs the nightly backup copy and, once sources are automated, `pn refresh --due` weekly. `PN_DATA_ROOT` and full paths are set explicitly.
- **Not needed:** `make` or `just` (optional). Dagster or Prefect only make sense past ~100 assets or several machines.

### 6.9 Environment
`uv` 0.13, Python 3.13, one `pyproject.toml` and `uv.lock` for the hub. `projects/<slug>/` code uses the hub environment or PEP 723 inline scripts. The crash app's `.venv` and `node_modules` leave OneDrive when its repo is re-cloned onto the PC.

### 6.10 Cloud path (not planned for now; kept for later)
- **Cloudflare R2.** $0.015/GB-month with free egress; 10 GB free. At ≈10–25 GB that's **$0–0.25 a month**.
- **Backup.** `rclone copy --immutable` for the append-only layers; `sync` only for marts.
- **Same queries, remote data.** `pn catalog --remote` writes `catalog_remote.sql` pointing at `r2://…`. Queries stay the same; what changes is which catalog file *and which secret* you load.
  - R2 needs a secret in each session, and DuckDB's persistent secrets are stored unencrypted under your profile.
  - Public marts can use a custom-domain `https://` URL instead, since `r2.dev` URLs are rate-limited.
- **Options:**
  - MotherDuck Lite ($0 tier): hosted SQL from any device.
  - Hugging Face: free public home for data packs.
  - Backblaze B2: an alternative to R2.

**Fly.io note.** New organisations no longer get a free tier. Check your bill. Static hosting (Cloudflare Workers static assets + R2 + DuckDB-WASM or precomputed JSON) is the near-zero-cost option for future apps that don't need server-side aggregation.

### 6.11 "Don't store anything, just call APIs"
Rejected as a *general* policy:
1. Key sources have no API: MDSP, JCHS, PDFs, Power BI.
2. Sources revise and roll off history: AADT's oldest year is already null; Zillow re-smooths.
3. Reproducing published numbers needs frozen inputs.
4. Some APIs are slow or capped at your scale.

Adopted where it fits: cache-through and the logged live mode (§3.4).

---

## 7. Data quality and integrity standards

### 7.1 Intake checks (every snapshot)
- Not empty.
- Content type matches. This catches SBE's soft-404 HTML pages.
- Header signature matches; a new or dropped column warns and needs approval.
- Encoding detected.
- Row count within a band of the prior snapshot for the same period.
- Date coverage matches the declared period.
- Coordinates inside the MD/DMV bounding box.
- Duplicate keys reported.
- Hash unchanged → skipped.

### 7.2 Build checks seeded from the investigation

| Check | Safeguards against |
|---|---|
| ACRS vehicles per report per batch ∈ [1.5, 2.5]; persons per report in a plausible band | #4 (truncated export) |
| Every vehicle and person report number exists in `acrs_report`. Orphans ≤ 0.5% warn, above that error. Entities for a period come from one export session. | #9 |
| Per-tract polygon area (EPSG:26985) ÷ (ALAND + AWATER) ∈ [0.99, 1.01]; `*_km2` columns plausible | #5 (CRS unit) |
| FARS person type mapped through `ref.fars_codes`: non-motorist = `per_typ IN (4,5,6,7,8,10,19)`, verified per year against the FARS manual; never "not a driver" | #2 |
| No build output with zero rows unless allowed | #7 |
| Positional or name keys resolved to IDs in staging; unresolved count reported | #6 |
| AADT current-year column: if it equals exactly one `AADT_<year>`, assign that year. If it matches none, assign max+1 and require `--confirm-year`. Record the method. | AADT drift |
| ACS: MOE present, sentinels nulled, vintage present | ACS aggregation errors |
| Totals vs published anchors: statewide fatalities vs FARS/MDOT, MD population vs Census | Silent join loss |

### 7.3 The metric library
`catalog/metrics.sql` holds DuckDB macros, documented in `metrics.md`; Python calls the same SQL. Each metric declares its formula, unit, a **window rule** and a label template. Starting set:
- `rate_per` and `annualized_rate`. Multi-year counts must say "cumulative, k years" or be annualized.
- `deaths_per_100m_vmt`, with VMT summed over the *same* years as the deaths.
- `vmt`, `lane_miles`, and length-weighted `vmt_per_lane_mile`.
- `to_real_dollars` (CPI-U NSA `CUUR0000SA0`). Default target: annual average. Method-specific targets are allowed.
- `index_to`, `yoy`.
- `acs_sum_moe`, `acs_ratio_moe`, `median_from_bins`.
- `share`, with an explicit denominator.

### 7.4 Methodology versioning
Modelled datasets carry a `method_version`.

`crash.report_cost` method **2026.1** reproduces the published model:
- NHTSA 2019 Table 1-10;
- CPI-U **June 2019 → June 2025**, computed from `econ.cpi_u` (≈1.259; a `legacy_factor: 1.26` parameter allows exact parity);
- ACRS injury → MAIS map v1;
- PDO costed per vehicle.

No method change is planned (decision E2). Any future method (e.g. an annual-average deflator) would get a new version and a changelog entry.

### 7.5 Sensitivity and licensing
- Columns tagged `pii` can't be exported by `pn pack` without an override. These include crash-person demographics, NIBRS victim fields and addresses, licence plates and GPX traces.
- Datasets with `redistribution: not_allowed` (likely Zillow, pending its terms) are excluded from public packs; the pack README says how to obtain them.

---

## 8. Conventions (summary; full text in `catalog/conventions.md`)

- **Names**
  - `snake_case`.
  - IDs follow `<domain>.<dataset>` with singular nouns.
  - Prefixes and suffixes: `is_*` / `has_*` for booleans, `n_*` for counts, `*_usd<year>` for money, `*_per_<n>` for rates.
  - Raw paths use `<source>/<entity>`.
- **Keys**
  - `geoid` (text) + `geoid_vintage`.
  - `report_number` (ACRS, upper-case, trimmed).
  - `(fars_year, st_case)`.
  - `person_id`.
  - `(session, bill_number)`.
  - `(election_id, contest_id)`.
  - `route_id` + `route_id_gtfs`.
- **Time**
  - `date` / `month` / `year` / `period_start` / `period_end` for what a row describes.
  - `vintage` for the edition.
  - `retrieved_at` in UTC.
  - Timestamps stored in UTC with the local zone documented. NIBRS arrives in UTC; convert it in staging.
- **Codes.** Keep the source code and add a label from `ref.*`. Never collapse codes into binaries in staging.
- **Geometry.** OGC:CRS84 stored; EPSG:26985 measured; `_display` geometry never used for analysis.
- **Files.** Raw keeps original filenames. Builds are `build=<id>.parquet`, partitioned only above ~1 GB (FARS by year).

---

## 9. What happens to today's data

The per-file register is `appendix_dataset_register.csv`; it lists existing datasets plus proposed additions.

| Disposition | Datasets |
|---|---|
| **Adopt as-is: intake existing files into `raw/`, then stage** | MDSP ACRS 2024H1–2025H2 (all four entities, using the fixed H2-2025 vehicles file, with a legacy mixed-session waiver: §10); NHTSA unit-cost table → seed; the crash app's simplified GeoJSON → `geo.*_display`; MTA Power BI JSON pulls (first snapshot); MGA bill CSVs 2023–26; HAC questionnaire JSON; JCHS appendix + rent-burden CSV (with provenance note); Baltimore NIBRS export (first snapshot); WMATA 2025 entries; station points (after provenance check); FARS 1975–2023 zips (flattened once, de-duplicated) |
| **Re-derive in the hub, with parity tests** | `crash_cost_eval.csv` → `crash.report_cost` method 2026.1 (210,860 rows; 2024 = $41.04B, 2025 = $37.34B); geo summaries → `crash.summary_*`; BVA tract panel → mart (after the unit fix) |
| **Re-acquire systematically** (details in `02`) | TIGER: state files for tract/BG/place, national-filtered for county/ZCTA; NHGIS ACS extracts → `census.acs5` via the Census API; DHC P1 → API; density workbooks → Gazetteer land area + population; AADT ×3 → FeatureServer annual snapshots with explicit years (Feb and Oct 2026 statewide files kept as history; the Jul BVA copy is a city clip only); Zillow → dated CDN pulls; FRED CSVs → BLS LAUS / FRED with series IDs; PEP/BPS → www2 files; MoCo crashes → Socrata; NIBRS → FeatureServer; SBE HTML scraping → `GP26_*`/`GG26_*` CSVs; BillMasterList.csv → `legislation.json`; Open States roster → CSV + YAML; MTA bus lines → GTFS shapes (+ iMAP layer 10); WMATA entries → Tableau `.csv` URL |
| **Retire (after your confirmation)** | `source/Perfect-Numbers/apps/data` (stale; contains the bad file); FARS nested duplicates and re-saved zips; concatenated `*_maryland_2024_2025.csv`; national shapefile caches and nested zips; `zhvi_eastern_silver_spring.xlsx`; the unused FHFA file; hand-built Excel derivatives once replaced; the stray installer |
| **Leave in projects** | Photos, video, GPX (unless you want a `field` domain), drafts, piece-specific LLM summaries, figures, regression outputs |

**New datasets come in only when a piece needs them (D4).** Given your queue (§0.2), these are needed first:
- **Bus-corridor piece:**
  - MTA local-bus GTFS (snapshotted);
  - MTA stop-level boardings (iMAP `MD_Transit/9`);
  - MTA route-month ridership (Power BI connector);
  - Baltimore City street centerline (city ArcGIS, `Street_Centerline_Native`);
  - road jurisdiction (MDOT SHA *Roadway Maintenance Responsibility* / *Know Your Roads*);
  - BCDOT bike facilities;
  - an existing-bus-lanes list. No public layer was found, so it comes from OpenStreetMap `busway`/`lanes:bus` tags or a hand-built seed.
- **I-83 / ReVision Zero #3:**
  - the crash slice (with parity);
  - AADT annual snapshots;
  - FARS through 2024;
  - `econ.cpi_u`;
  - an I-83 corridor custom area;
  - optionally fresh 2026 crash months from MDSP.
- **Later (traffic violence × crime):** Baltimore NIBRS mirror; BVA migration with the unit fix.
- **Watch, don't build:** ACS 2021–25 (may slip under DAO 216-26); `pn status` flags it when it appears.

---

## 10. Roadmap

The order follows your queue: the bus-corridor piece now, I-83 next. Effort is a rough estimate of agent-assisted hours; your share is mostly review, decisions and manual downloads. Nothing destructive happens without your explicit go-ahead.

### Phase 0 — Housekeeping and the new repo (≈ 4–6 h, mostly you)

**1. Secrets.**
- Rotate the IPUMS key.
- Create `%USERPROFILE%\.config\pn\.env`.
- Get a Census key (now mandatory) and a BLS key.

**2. New pipeline-first repo (non-destructive).**
1. On GitHub, preserve the current history: tag `origin/main` as `archive-2024-2026`, or keep it on a branch of that name.
2. Create the new repo on the PC at `C:\Users\Matt\code\perfect-numbers`, with the §3.1 layout, a root `.gitignore`, a new README and this design folder under `docs/design/`.
3. Publish it as the new `main`. This step replaces the default branch on GitHub, so I'll show you the exact commands and wait for your OK.

**3. Archive the old layout.**
- The OneDrive `Perfect-Numbers` folder stays as-is and becomes a read-only archive. Its unpushed commit `3d29916` is simply never pushed.
- The `source/` clone is retired after you confirm.
- The crash app's repo is re-cloned onto the PC; its `.venv` and `node_modules` stay out of OneDrive.

**4. Environment.**
- Install `uv` and DuckDB 1.5.6.
- Create `PN_DATA_ROOT`.
- Add the nightly backup task (one-way `robocopy` of the append-only layers into OneDrive).

**Exit:** the new repo is on GitHub with no data files, keys load from one place, and the backup task runs.

### Phase 1 — Foundation + bus-corridor slice (≈ 25–35 h; feeds the piece you're writing now)

**1. Foundation**
- **`pndata` skeleton:** paths, manifests, the build and test runner, catalog generator.
- **Connectors:** `manual`, `http_file`, `arcgis`, `census_api`, `rest_json`.
- **CLI:** `status`, `fetch`, `intake`, `build`, `check`, `catalog`, `describe`, `export`.
- **Agent setup:** `AGENTS.md` + `CLAUDE.md`; the read-only DuckDB MCP server for Claude Desktop and Cursor.

**2. Geography (Baltimore City + MD)**
- TIGER 2024 tract and place state files; county from the national file, filtered; Gazetteer land area.
- `ref.county_codes`, `pn.geo.assign`.
- The GeoParquet-writer spike.

**3. Streets and jurisdiction**
- `traffic.street_segment` from Baltimore City's centerline.
- `traffic.road_jurisdiction`: MDOT SHA maintenance responsibility, joined to segments. This shows which corridors the city controls, the core of the piece's argument.
- BCDOT bike facilities.
- An existing-bus-lanes seed, from OpenStreetMap tags plus hand corrections.

**4. Transit**
- `transit.gtfs_mta` local-bus snapshot.
- `transit.stop_ridership` (iMAP layer 9, Summer 2024 weekday boardings).
- MTA route-month ridership through the `powerbi_public` connector, wrapping your existing decoder, including `route_id_gtfs` for the join.
- `transit.ntd_monthly` as the official cross-check.

**5. Mart: `transit.bus_segment_service`.**
- **Grain:** street segment × time band (AM peak, midday, PM peak, evening; weekday/weekend).
- **Method:** map each GTFS shape onto street segments, then count scheduled trips, distinct routes and buses per hour on each segment. Estimate riders from stop boardings along the segment, with route-month ridership as a scaling check.
- **Attributes:** jurisdiction, lanes, existing bus or bike facility.
- **Caveats:** stop boardings are for Summer 2024 and are not route-specific. Segment ridership is therefore an estimate, and the card says so.

**6. Docs:** generated `CATALOG.md`, dataset pages, `conventions.md`, and 3–5 example queries (e.g. "top 20 city-controlled segments by buses per peak hour").

**Exit tests:**
- `transit.bus_segment_service` totals reconcile with GTFS: scheduled trips per route are conserved after segment mapping.
- An agent in a fresh session answers *"Which city-controlled street segments carry the most buses per peak hour?"* from the catalog alone.
- `pn status` is green.

### Phase 2 — I-83 / ReVision Zero #3 slice, including the crash parity test (≈ 25–35 h)

**1. Crash data.**
- Intake the 16 existing MDSP files, reconciled against the `.csv` endpoint. Record a `legacy_mixed_session` waiver for 2025-H2: Reports came from 2026-03-28, Vehicles from 2026-06-06.
- Build staging with the §7.2 checks, then `crash.report_geo`, `crash.report_cost` (method 2026.1, `econ.cpi_u`), and `crash.summary_*`.

**2. Parity.**
- `crash.report_cost` must match `crash_cost_eval.csv` row-for-row, with `legacy_factor: 1.26`.
- The summaries must match `merged_*.csv`.
- `pn export app:crash-cost-md`, diffed against today's `data_cache/`.

**3. MDSP automation, API route first** (you asked for an API call over Playwright).
- A ~4 h spike tests Tableau's guest-session export routes:
  - the crosstab and underlying-data export commands the "Download" menu calls;
  - per-sheet `.csv` on the hidden worksheets with different view paths;
  - Tableau's `:format=csv` view variants.
- If none returns row-level data, fall back to Playwright.
- Either way, exports use **monthly windows, or weekly if the Data option stays greyed out**, which looks like a record-count limit. They cover **all tabs and all fields**, all in one session.
- Then pull 2026-H1 (and later months) through the new route, and re-export 2025-H2 in a single session.

**4. Corridor data.**
- AADT annual snapshots (FeatureServer, explicit years), and exposure marts: VMT, lane-miles, length-weighted volume per lane-mile.
- FARS 1975–2024 (Annual Report File) to Parquet; `ref.fars_codes`; `crash.fatal_combined`.
- An I-83 corridor custom area (buffer around JFX/I-83 in Baltimore City and Baltimore County).
- The Baltimore County crash mirror (ArcGIS; same report numbers) as a cross-check.

**5. Publishing.** `pn pin`, `pn pack`, `pn.publish`; register the posts and charts; build a retroactive pack for post 9.

**Exit tests:**
- Both parity tests pass.
- The pre-registered answer holds: Howard County 2025 cost per resident ≈ **$3,864** ($1.2995B ÷ 336,328, ACS 2020–24).
- An agent in a fresh session can produce I-83 crash counts, costs and deaths per 100M VMT with matching windows.

### Phase 3 — Backlog pulled by later pieces

| Item | Rough effort | Trigger |
|---|---|---|
| Baltimore NIBRS mirror (UTC → local) + BVA migration (unit fix) | 4–6 h | Traffic violence × crime |
| Document library intake; OCR on demand | 3–5 h | When documents are reused |
| `geo.custom_area` + proper ACS aggregation (medians, MOEs); DC/VA geography; IPUMS client | 4–6 h | ESS / Purple Line pieces |
| MoCo crash Socrata mirror | 2 h | Montgomery pieces |
| Zillow dated pulls; BLS LAUS; FRED | 2–3 h | Housing/economy pieces |
| WMATA entries; Ride On GTFS; station crosswalk | 3–4 h | Purple Line |
| Politics backbone (SBE, MGA `legislation.json`, Open States) | 8–12 h | Only if politics pieces return |
| Task Scheduler `pn refresh --due` for automated sources | 1–2 h | Once MDSP / GTFS / ridership are automated |
| Evaluate DuckLake and DuckDB 2.x; first Claude skill | — | When useful |

## 11. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| The hub becomes a project in itself and slows writing | Medium | Phase 1 is one slice; Phase 2 is demand-driven; time budget (A5); minimum-viable fallback (§6.6) |
| The custom runner becomes a maintenance burden | Medium | Keep it small; cards and SQL stay dbt-compatible; switch when the triggers in §6.6 hit |
| DuckDB 2.0 breaking changes | High (Oct–Nov) | Pin `<2`; the catalog is a regenerated SQL file |
| MDSP has no clean API; the export UI changes | Medium | Manual intake with reconciliation; API-route spike, Playwright fallback; smaller export windows; MoCo/BaCo/FARS cross-checks; bulk access via MSP or an MPIA request remains an option you have chosen not to pursue for now |
| Undocumented Power BI endpoint breaks | High eventually | Mirror every pull; drift check; NTD as the official fallback |
| Federal data degradation (DAO 216-26 delays and coarsening) | Medium–High | Cache-through keeps every slice used; NHGIS keeps older vintages; cards make missing vintages visible |
| Agents make confident but wrong changes | Medium | Writes only via `pn`; checks gate promotion; raw read-only + hash checks; cards required |
| Data root lost | Low | Append-only layers backed up one-way; manifest committed; marts rebuild |
| Storage growth from frequent snapshots | Medium | Skip unchanged hashes; compress raw text; per-source retention (e.g. weekly NIBRS thinned to monthly after 90 days, as declared in the card); packs keep what was published |
| Licensing violation in public packs | Low | `redistribution` flag enforced by `pn pack` |

---

## 12. Requirements cross-check

| Requirement | Met by |
|---|---|
| R1 reference, don't copy | §3.1, §3.5, §5.1 |
| R2 acquisition-agnostic | D2, §5.5 |
| R3 provenance | §3.2, §5.3 step 4, §5.2 reproducible rebuilds |
| R4 explicit time | D5, §8, §7.2 AADT rule |
| R5 scope | D4, §3.6, §5.3 step 3 |
| R6 geography | §3.6 |
| R7 politics entities | §3.7 |
| R8 checks | §7.1–7.2 |
| R9 metrics | §7.3 |
| R10 AI-legible docs | §4 |
| R11 publish freeze | §5.1 (pin), §5.4 (pack) |
| R12 secrets / PII | §5.3 step 4 (redaction), §5.6, §7.5 |
| R13 solo / local / cloud-ready | §6, §10 effort estimates |
| R14 documents | §3.8 |
| R15 hygiene | §10 Phase 0 |

---

## Glossary

- **Raw / staging / marts.**
  - *Raw* is exactly what a source served.
  - *Staging* is one cleaned table per source entity.
  - *Marts* are joined or derived tables that projects use.
- **Snapshot.** One retrieval of a source, stored unchanged under `raw/`, with a manifest line.
- **Build.** One run of `pn build` that produces a versioned Parquet file for a dataset.
- **Pin.** A project's record of which build of each dataset it uses.
- **Data pack.** The frozen outputs and inputs behind a published piece.
- **Card.** The YAML file describing a dataset, which is its contract. A **source card** describes a publisher and endpoint.
- **Vintage vs period.**
  - *Vintage* is the edition, such as ACS 2020–24 or PEP V2025.
  - *Period* is the time the rows describe.
- **Access modes.**
  - *Mirror* stores snapshots on a schedule.
  - *Cache-through* fetches a slice on first use and keeps it.
  - *Live* is exploration only.
  - *Manual* means you download the file.
  - *Derived* means built by the hub.
- **Seed.** A small hand-maintained reference table kept as a CSV in git.
- **Parity test.** Rebuilding an existing published dataset in the hub and proving the numbers match.
- **Crash, transport and statistics terms.**
  - *MOE*: an ACS margin of error.
  - *PDO*: a property-damage-only crash.
  - *MAIS*: NHTSA's injury severity scale.
  - *KABCO*: police injury scale (killed, A/B/C injury, no injury).
  - *ARF*: FARS Annual Report File, provisional until the Final file.
- **Tool and AI terms.**
  - *ADR*: a short decision record.
  - *MCP*: Model Context Protocol, a way for AI apps to query tools such as a database.
  - *Exposure (traffic)*: the amount of travel crashes are compared against: VMT, lane-miles.
