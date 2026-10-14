# 01 — Investigation: what data exists, how it's used, and where it hurts

Status: complete · Date: 2026-10-12 · Method: read-only audit of every folder under `2025/`, `2026/`, `data/` and `source/`, plus all 10 published posts on perfectnumbers.substack.com (text, links, and the 15 Datawrapper charts with their source CSVs). Nothing outside `data/admin/design/` was modified. Every bug or discrepancy listed in §6 was re-verified by hand, not just reported by an audit agent.

---

## 1. Summary

1. **The blog has become a Maryland data desk.** Since January 2026 it has published 7 posts in 9 months on road safety, transit, housing/land use, and local elections, plus a public app (crash-cost-md.fly.dev). The same few datasets recur:
   - Census ACS/decennial and TIGER boundaries, in 3+ posts and 8 project folders.
   - Maryland crash records, in 3 posts and 5 folders.
   - MDOT SHA AADT, in 3 folders.
   - Zillow ZHVI, used by 3 projects and stored in 2 of them.
   - MGA/SBE politics data, in 2 posts and 3 folders.
2. **Data moves between projects by copying, not by reference.**
   - The Baltimore project hand-copied a filtered crash parquet and boundary files, with no script.
   - us29_review byte-copied a FARS extract from pedestrian_deaths.
   - Post 7's Zillow chart reads from the `planning_open_house` folder.
   - A 2.9 GB stale copy of crash_costs' inputs in `source/` (0.8 GB of crash exports plus 2.1 GB of national census shapes) still contains the known-bad H2-2025 vehicle file.
3. **About 14 GB of the ~24 GB of project data is reclaimable.** That is roughly 9.5 GB of *national* boundary files serving Maryland/DMV questions (the Maryland/DMV equivalent is under 100 MB), 3.3 GB of duplicated FARS files, and ~1 GB of stale or concatenated crash copies. Separately, git holds ~8 GB of loose objects from an unpushable local commit.
4. **The same Census tables are re-extracted per project.**
   - There are 8 NHGIS extracts on disk. ACS 2020–24 B01003 was pulled 4 times and B19013 3 times.
   - Two separate IPUMS API clients disagree on auth variable names and CSV header handling.
   - Five of the 8 extracts were made by hand on the website, with no record of their definition.
   - County population comes from three different sources in three projects (PEP V2024, 2020 DHC, ACS 2020–24).
5. **Vintage and meaning drift is invisible.**
   - The MDOT SHA AADT field `AADT` (no year suffix) means 2024 in two of the copies on disk and ≈2025 in the newest (October) copy.
   - Zillow snapshots carry no date.
   - TIGER boundaries exist in 4 vintages (2020, 2023, 2024, 2025).
6. **Most acquisition is manual and undocumented.** Dashboard exports, ArcGIS Hub downloads, NHGIS web extracts, FRED downloads and PDF copies have no URL, date or hash recorded. Three exceptions should become the standard:
   - `baltimore_violence_association` (BVA) has fetch scripts with JSON manifests.
   - `purple_line` has a hash-keyed NHGIS cache.
   - `mta_overview/data-acquisition-plan.md` is an excellent source spec.
7. **Quality problems are caught late or not at all.** §6 lists 9 verified issues. Each maps to a safeguard in the proposal:
   - automatic intake and build checks: #4 (row ratio), #5 (CRS units), #7 (no empty outputs), #9 (referential integrity);
   - shared definitions and reference tables: #1 (metric window rules), #2 (FARS code table), #6 (typed IDs, no positional keys);
   - a publish-time review and chart registry: #3 (chart versions), #8 (seasonal adjustment).
8. **Good practices already exist but are siloed.** Examples: BVA's `src/paths.py` and manifests, purple_line's `DECISIONS.md` and `ISSUES_LOG.md`, crash_costs' `DATA.md` reproduction table, the MTA workbook's README and validation sheets, saved LLM prompts in the election projects. The central repo should make these the default.
9. **Repo hygiene blocks everything else:**
   - No root `.gitignore`.
   - An unpushed commit (`3d29916`) adds 1,817 files including FARS and >100 MB shapefiles.
   - Three diverged copies of the crash app, two nested repos, and environments (`.venv`, `node_modules`) inside OneDrive.
   - An IPUMS API key in two project folders. The project's own issues log notes it was once pasted into a doc, so it should be rotated.

---

## 2. What the blog publishes (and therefore needs)

| # | Date | Post | Folder | Data it rests on |
|---|---|---|---|---|
| 1 | 2024-10-22 | Welcome to Perfect Numbers | 2025/welcome… | none |
| 2 | 2024-10-29 | The 52nd Perfect Number | 2025/the_52nd… | Prime Pages list (hand-built CSV) |
| 3 | 2025-03-27 | 2025 Orioles Offseason Review | 2025/orioles… | FanGraphs (hand-built xlsx) |
| 4 | 2026-01-16 | ReVision Zero: A 100 Foot Death Wish | 2026/georgia_ave | dataMontgomery crash incidents; zerodeathsmd fatal dashboard; NHGIS ACS 2019–23 + 2020 DHC tract density; NSC mode death rates; WMATA ridership *(not in repo)* |
| 5 | 2026-03-09 | ReVision Zero: US-29 | 2026/us29_review | MDOT SHA AADT segments; FARS 2019–23 + HoCo MSP export + MoCo open data fatals; GPX drives; 2020 DHC county density |
| 6 | 2026-04-29 | Eastern Silver Spring plan preview | 2026/planning_open_house | ACS 2020–24 DP04 over 8 plan-area tracts; plan PDFs |
| 7 | 2026-05-11 | MoCo can't afford stagnation | 2026/moco_election_endorsements | FRED/LAUS unemployment; Zillow ZHVI (neighborhoods) *(stored in planning_open_house)*; Banner poll *(typed into Datawrapper)*; questionnaires |
| 8 | 2026-05-22 | 2026 HoCo Primary Guide | 2026/hoco_elections | PATH/HAC/Chamber questionnaires; SBE 2022 result *(not in repo)* |
| 9 | 2026-06-13 | Crash costs: $37.3B in 2025 | 2026/crash_costs | MDSP ACRS 2024–25; NHTSA 2019 unit costs ×1.26; ACS 2020–24 via NHGIS; TIGER 2024; app |
| 10 | 2026-09-18 | 2027 is a critical juncture for the MTA | 2026/mta_overview | MTA Power BI ridership 2016–2026; MGA bills; budget documents |

**Unpublished but data-heavy:**
- `baltimore_violence_association`: tract panel of crashes, crime, AADT and ACS, with regressions.
- `purple_line`: station catchments and a ridership model.
- `md_rental_market`.
- `maryland_housing`.
- `pedestrian_deaths`: FARS national plus a DC navigator app.
- The legislative-turnover dataset in `mta_overview/work`.

**Cadence and timeliness.** There are two working modes:
- **News-reactive pieces**, published within days to weeks of an event. They use data 1–2 months old: FRED, Zillow, MTA ridership, local crash data.
- **Long-form tools and analyses**, such as the crash app and the Baltimore and Purple Line work.

So monthly feeds need refresh-on-demand in minutes, and annual datasets need clear vintage tracking.

**Promised and likely next pieces.** ReVision Zero #3; the ESS opinion piece (promised twice); MTA follow-ups through the 2027 session (HB517 study due Dec 1; BMore Bus; Red Line; Purple Line opening Jan 2028). Annual data refreshes are also due: 2026 crash data, FARS 2024, AADT, and ACS 2021–25.

**Publishing layer.** All 15 Datawrapper charts are the de facto output layer. Three posts embed an earlier chart version than the one now live (`N1hP3`, `6aI4r`, `q8aDD`). Old version URLs redirect to the latest version, so web and email readers can see different charts. For `N1hP3` the numbers differ (Jan 2025 vs Jan 2026); for the other two, the newer version predates the post. Nothing records which data produced which chart version.

---

## 3. Canonical dataset inventory

One row per *real-world* dataset, de-duplicated across projects. The machine-readable version with paths and proposed disposition is `appendix_dataset_register.csv`.

### 3.1 Crash and road safety

| Dataset | Publisher | Acquired today | Where (projects) | Vintage on disk | Grain / key |
|---|---|---|---|---|---|
| ACRS crash exports: Reports, Vehicles, Occupants, NonMotorists | MD State Police (dashboard) | Manual half-year CSV export | crash_costs (canonical); stale copy in `source/`; HoCo fatal subset in us29 | 2024H1–2025H2 | report `Reportnumber`; vehicle `ReportNumber Veh`+`VehicleID`; person `ReportNumber Occ/NM`+`PersonID` (the key column is named differently in each file) |
| MoCo Crash Reporting – Incidents (ACRS-based) | Montgomery County (Socrata) | Manual portal export | us29, georgia_ave | 2015 → Jan 2026 (fatal subset) | `Report Number`, the **same ACRS key**: 73/74 of 2024–25 fatal crashes match crash_costs |
| FARS national (accident, person, vehicle + ~30 auxiliary tables) | NHTSA | **Scripted** bulk zip download | pedestrian_deaths; byte-copied extract in us29 | 1975–2023 (2024 missing) | `(year, st_case)`; `veh_no`, `per_no` |
| NHTSA *Economic & Societal Impact 2019 (Revised)* unit costs | NHTSA | PDF → hand-transcribed xlsx | crash_costs | 2019 $ | injury category × cost component |
| MD crash-level comprehensive cost table (**derived**) | — | `crash_costs.ipynb` | crash_costs → app → BVA (Baltimore slice) → blog scripts | 2024–25, 2025 $ | `report_number` |
| zerodeathsmd fatal dashboard figures; NSC Injury Facts mode rates | MDOT HSO; NSC | Read off dashboards / hand-typed | georgia_ave | — | — |

### 3.2 Traffic, roads and transit

| Dataset | Publisher | Acquired today | Where | Vintage on disk | Grain / key |
|---|---|---|---|---|---|
| AADT points (layer 0) and segments (layer 1) | MDOT SHA (ArcGIS FeatureServer) | Hub download ×2; **API** ×1 (BVA `src/aadt.py`) | us29 (Feb), BVA (Jul, city clip), `data/md_aadt` (Oct) | AADT_2015–2024 plus `AADT` for the "current" year, which differs by copy | station `LOCATION_ID`; segment `GlobalID`/`OBJECTID` (unstable); `ROUTEID_RH` + mileposts |
| MTA bus route lines | MTA / MD iMAP | Hub download | `data/mta` | undated | `Route_Number` (+ needs a CityLink crosswalk) |
| MTA ridership by mode and route, monthly | MTA Customer Experience dashboard (Power BI) | Reverse-engineered `querydata` API, plus a legacy page scrape | mta_overview | mode 2011–2026-07; route 2013–2026-07 | `route_id`, `mode_id`, `month_start`; `route_id_gtfs` exists but wasn't pulled |
| WMATA station entries 2025 | WMATA Ridership Portal (Tableau) | Manual export | purple_line | 2025 | station name (27-entry hand crosswalk) |
| Metro and Purple Line station points | DC GIS (probably); unknown | Manual | purple_line | 2022 / unknown | name |

### 3.3 Census, boundaries and demographics

| Dataset | Publisher | Acquired today | Where | Notes |
|---|---|---|---|---|
| ACS 5-year 2020–24 detailed tables | Census via IPUMS NHGIS | 2 web extracts (national) + 2 API extracts (MD; DC/MD/VA) | crash_costs (0008), planning_open_house (0010), BVA (0011), purple_line (0012) | ~30 distinct tables; heavy overlap; NHGIS column codes (e.g. `AUO6E001`) differ from Census codes (`B01003_001E`) |
| ACS 2019–23 B01003 (tract) | NHGIS | web extract (national) | georgia_ave (0003) | superseded vintage |
| 2020 Decennial DHC P1 (tract, county) | NHGIS | web extracts (national) | georgia_ave (0004), us29 (0007) | turned into density percentiles **by hand in Excel** |
| Census PEP V2024 population and housing units; Building Permits 2024 | Census | manual xlsx | maryland_housing | hand-cleaned into `modified/*.xlsx`, dropping FIPS codes |
| TIGER/Line tract, county, place, block group | Census (direct or via NHGIS) | national zips, ×4 vintages | crash_costs, source/, purple_line, pedestrian_deaths, us29 (downloaded on every run) | **~9.5 GB total, MD/DMV share <100 MB** |
| MD 2020 tracts | MD iMAP | manual | planning_open_house | 6 MB |
| Simplified MD county/place/tract GeoJSON (**derived**, display-grade) | — | `prepare_data.py` | app; reused **as analytical boundaries** in BVA | should be labeled display-only |

### 3.4 Housing and economy

| Dataset | Publisher | Acquired today | Where | Notes |
|---|---|---|---|---|
| Zillow ZHVI (state, county, metro, neighborhood; mid-tier, SA, smoothed) | Zillow Research | manual CSV | maryland_housing (to Sep 2025), planning_open_house (to Mar 2026) + an 89.5 MB xlsx holding the whole national file | snapshots undated; used by post 7 from another project's folder |
| FHFA HPI master | FHFA | manual | maryland_housing | **unused** |
| JCHS America's Rental Housing 2026 (+ hand-copied rent-burden map data) | Harvard JCHS | manual | md_rental_market, stale copy in `source/` | no API |
| FRED/LAUS unemployment (MoCo, MD, US) | BLS via FRED | manual CSV, columns renamed | moco_election_endorsements | **seasonally adjusted and unadjusted series mixed**; series IDs lost |
| CPI (inflation) | BLS | hard-coded factor 1.26 | crash_costs; "real ZHVI" in post 7 | no deflator table |

### 3.5 Politics, elections, legislature

| Dataset | Publisher | Acquired today | Where | Grain / key |
|---|---|---|---|---|
| MGA bill master lists, 2023–2026 RS | Dept. of Legislative Services | **bulk CSV** (`…/{yyyy}rs/misc/billsmasterlist/BillMasterList.csv`) | mta_overview/work | `(session, bill_number)`; sponsors are free text (78% resolved) |
| Legislator roster | Open States (CC0) | live CSV, not saved | mta_overview/work | `ocd-person` id; MGA slug (changes when a member switches chamber) |
| Committees, member bios (Maryland Manual) | MGA / MSA | HTML scrape, not saved | mta_overview/work | committee code × slug; bios keyed by **display name** |
| SBE 2026 candidate lists | MD State Board of Elections | live CSV, **never saved**; one copy read off HTML by an LLM | mta_overview/work, hoco_elections | name + office + district |
| SBE 2026 primary results | SBE | HTML scrape of 118 pages | mta_overview/work | page **index used as district key** (bug, §6) |
| Candidate questionnaires (PATH, HAC, Chamber, GGWash, Montgomery for All) | advocacy groups | scrape / URL-guessing / copy-paste | hoco_elections, moco_election_endorsements | candidate × question; Chamber PDFs are scanned (no OCR) |
| Recommendations / endorsement tables (**derived**) | author + LLM | hand + LLM | hoco_elections | no person IDs |

### 3.6 Crime

| Dataset | Publisher | Acquired today | Where | Notes |
|---|---|---|---|---|
| Baltimore NIBRS Group A crime | Open Baltimore (ArcGIS Hub) | manual export | BVA | 260k rows, 2022→; UTC timestamps not converted; victim demographics + block address (sensitive) |

### 3.7 Documents (a large, unmanaged share of the sources)

About 300 MB of PDFs:
- Master plans and ESSCP preliminary recommendations.
- NHTSA cost report, ACRS field reference, FARS manual.
- JCHS report.
- OLA MTA audit, MCPD crime report, HB0517 enrolled bill, Transit Caucus letter.
- 31 questionnaire PDFs.

Only some have extracted text, and none have a recorded source URL and date.

---

## 4. Recurring geographies, keys and metrics

**Geographies:**
- Maryland state and its 24 county-equivalents. The most frequent are Montgomery 24031, Howard 24027, Baltimore City 24510 and Baltimore County 24005.
- 1,475 MD tracts (2020 definitions) and block groups; 536 places/CDPs.
- DC/MD/VA for regional work.
- Custom areas built from tracts: the ESS plan area, station catchments, corridor buffers.
- Political districts: legislative 2022 plan, council districts.
- AADT road segments; Zillow neighborhoods.
- National state and county panels, used only for rankings.

**Join keys, and the dialects in use:**
- **Census:** `GEOID` (5/11/12-digit), NHGIS `GISJOIN`, long `1400000US…`/`GEOIDFQ`, `STATEA`+`COUNTYA`+`TRACTA`. Three separate converter functions exist.
- **Crashes:** the ACRS report number is a *universal* key across MDSP exports, MoCo open data and the derived tables. FARS uses `(year, st_case)` and needs fuzzy linkage to ACRS.
- **County codes:** FIPS vs MDOT `COUNTY_ID` (alphabetical, Baltimore City = 24) vs SBE numbering vs name variants.
- **Politics:** Open States id, MGA slug, MSA id, name aliases, district formats (`01A` / `12A` / "Legislative District 12A"), party spellings.
- **Transit:** `route_id` ↔ `route_short_name` ↔ `route_id_gtfs` ↔ geojson `Route_Number`; `mode_id` ↔ NTD mode code.

**CRS in use:** EPSG 4326, 4269, 3857, 2248, 26985, 26918, 6487, ESRI:102003. One of these was mishandled (§6).

**Metrics computed repeatedly by hand:**
- Per-capita and per-10k/100k rates.
- Crash comprehensive cost.
- VMT, lane-miles and VMT per lane-mile.
- Deaths per 100M VMT.
- Density with national percentiles.
- Tract → custom-area aggregation, often done wrongly: population-weighting medians, dropping margins of error.
- Inflation adjustment.
- Indexed/YoY time series.
- Shares by crash flag.

---

## 5. Storage, duplication and repo state

| Item | Size | Note |
|---|---|---|
| Project folders (2025, 2026) | ~21.3 GB | ~3.6 GB of it is photos and video |
| `source/Perfect-Numbers` clone | 3.0 GB | 2.9 GB of it is a stale untracked data copy (0.8 GB crash exports + 2.1 GB national census shapes) |
| Exact byte-duplicate files over 1 MB (non-media) | **5.9 GB** | biggest: FARS nested re-extraction (2.65 GB), crash/census copies in `source/`, purple_line's nested block-group zip |
| National boundary files (all copies) | **~9.5 GB** | MD/DMV equivalent < 100 MB |
| Working repo `.git` loose objects | **7.9 GB** | Unpushed local commit `3d29916`, message "Refactor the 52nd perfect number documentation for clarity and accuracy". It adds 1,817 files (≈49M lines), including FARS and >100 MB shapefiles. Branch `drop-blog-posts` is 1 ahead / 9 behind `origin/main`. |
| Environments in OneDrive | ~0.6 GB | crash app `.venv` 383 MB + `node_modules` 240 MB |
| Stray installer | 190 MB | `2026/crash_costs/data/Vehicles/GitHubDesktopSetup-x64.exe` |

**How publishing works today.** Work happens in the OneDrive repo. Finished pieces are hand-copied into the `source/` clone, which is what pushes to GitHub. The crash app was also split into its own repo (`mSorak/md_crash_costs`, nested in `2026/crash_costs/.git`). The result is three diverged copies of the crash app and no single source of truth.

**Secrets.** `2026/purple_line/.env` and `2026/baltimore_violence_association/analysis/config/ipums_api_key.txt` (contents not read). Each is gitignored by its own project, but there is no root `.gitignore`, and both sync to OneDrive. `purple_line/ISSUES_LOG.md` O6 records that the key was once pasted into `project_description.md`.

**Personal or sensitive fields** that must never be republished:
- MDSP occupant and non-motorist demographics (age, sex, city, ZIP).
- NIBRS victim fields and block addresses.
- GPX drive traces.

---

## 6. Integrity issues found (all verified)

None of these are anyone's fault. They are what any solo pipeline produces without automated checks. Each is listed with the safeguard that would have caught or prevented it, because §7 of the proposal is built from this list.

| # | Issue | Published? | Effect | Safeguard |
|---|---|---|---|---|
| 1 | **US-29 chart `Mv21f` unit label.** The footnote correctly discloses that 2023 traffic is paired with Jan 2019–Jan 2026 deaths. But the column labelled "Deaths per 100 Million VMT" holds 7 years of deaths ÷ one year of VMT in millions: HoCo 19/455.05 = 0.042, MoCo 29/244.2 = 0.119. | Yes (post 5) | Correctly scaled (2023 VMT × ~7.08 years) the values are ≈0.59 vs ≈1.68 per 100M VMT. The ≈2.8× ratio, which carries the argument, is unchanged. | Metric definition requiring numerator and denominator over the same window, plus publish-time label review |
| 2 | **US-29 passengers labeled "Non-Motorist".** `fatal_crash_data_processing.ipynb` maps FARS `PER_TYP != 1` to Non-Motorist. 17 HoCo and 28 MoCo passengers in the 2019–23 FARS rows are affected. | Possibly (post 5's motorist/non-motorist split) | Depends on which fall inside the 400 m buffer. **Re-check recommended.** | Enumerated-code mapping kept as a shared, tested reference table |
| 3 | **MTA chart `N1hP3` embedded at a superseded version.** Post 10 embeds v1 (Jan 2025 totals; its stored caption and the email image say "Jan. 2025"). v2 (Jan 2026 totals) was published 2026-08-31, before the post went out on 2026-09-18, and the embed URL redirects to it. | Yes (post 10) | Web readers see Jan 2026 numbers under a Jan 2025 caption; email readers saw v1. The text's claim ("more than twice") holds in both. | Chart registry (ID + version + uploaded CSV) checked at publish |
| 4 | **H2-2025 ACRS vehicle export incomplete:** 938 rows for 53,416 reports. Caught by a manual audit and fixed; the stale bad copy survives in `source/` and in git commit `3d29916`. | Caught before post 9 | Would have cut Jul–Dec 2025 PDO costs | Batch ratio check: vehicles per report in [1.5, 2.5]; observed 0.018 |
| 5 | **BVA unit bug.** EPSG:6487 is metres, but `enrich_panel.py` converts as if feet (area × 0.3048², length × 0.3048). | No | Areas 10.76× too small, lengths 3.28× too small. All three exposure/density covariates in the regression ladder are mis-scaled; coefficient sizes are wrong, OLS t-stats unchanged. | CRS-unit assertion; tract-area sum vs known land area (19.6 km² vs ≈210 km²) |
| 6 | **SBE primary results keyed by page index, not district.** In `margins.py`, the key `House_45` is actually District 33A. Later scripts match by name and are correct. | No | Wrong margins in an exploratory script | Typed IDs at ingest; no positional keys |
| 7 | **DC pedestrian navigator app is empty.** `app_data.csv` is header-only (24 bytes), written by a silent-failure path. | App is not public, as far as I can tell | Navigator shows nothing | "No empty outputs" build check |
| 8 | **Mixed seasonal adjustment.** FRED comparison CSV pairs MoCo `MDMONT0URN` (NSA) with MD/US seasonally adjusted series; the column renames dropped the series IDs. | Yes (post 7 chart `uUKYy`) | Minor visual inconsistency; the "highest since 2021" claim rests on the county series alone | Keep source series IDs as columns; catalog records adjustment |
| 9 | **H2-2025 Reports and Vehicles exports were pulled at different times** (Reports 2026-03-28; re-exported Vehicles 2026-06-06). The vehicles file (99,217 rows) references **194 report numbers that appear in no Reports file**, and 7 H2 reports have no vehicles. | Minor (post 9 / app) | About 0.4% of H2-2025 crashes are missing from the cost table | `relationships` test + "export all entities in one session" intake rule |

There are also ambiguities rather than errors. Post 9's per-capita figures are two-year cumulative values (the text does say "Between 2024 and 2025"). Post 5's "AADT per lane-mile" is an unweighted mean of segment ratios, so it is sensitive to how segments are split; weighting by length gives about 1.7× rather than about 1.76×. Standard metric definitions would make these explicit.

---

## 7. Practices already in the repo worth adopting everywhere

| Practice | Where it lives | Becomes |
|---|---|---|
| Fetch scripts that write a JSON manifest (URL/query, fetched_at, counts, fields) | BVA `analysis/03a_fetch_aadt.py`, `03b_fetch_nhgis.py` | The standard acquisition contract (proposal §5) |
| Hash-keyed extract cache; `extract_definition.json` written before submit | purple_line `src/nhgis_client.py`, BVA `src/nhgis.py` | The single IPUMS connector |
| Single path registry; env-var data root | BVA `src/paths.py`; app `CRASH_COST_DATA_DIR` | `PN_DATA_ROOT` + `pndata.paths` |
| `DECISIONS.md`, `ISSUES_LOG.md`, `analysis_plan.md` | purple_line | Per-dataset `NOTES.md` sections + ADRs |
| Reproduction table (step → command → output) | crash_costs `data/DATA.md` | Generated lineage in each dataset card |
| Data dictionary + methodology alongside the data | BVA `baltimore_traffic_data/`, crash_costs | Generated from dataset cards, never hand-maintained |
| Linkage audits written up with root cause | crash_costs `VEHICLE_LINKAGE_AUDIT.md` | Automated checks + a changelog entry |
| README sheet and validation sheets inside an output workbook | `MTA_Ridership_Data.xlsx` | Checks in the card; README in data packs |
| A verified source spec with hazards, validation targets and a schema | `mta_overview/data-acquisition-plan.md` | Template for source cards; seed for the politics domain |
| Prompts saved next to LLM outputs | hoco/moco election folders | LLM-extraction lineage standard (prompt + input hashes + output) |
| `run_metadata.json`, `variable_labels.csv`, `.meta.json` sidecars | planning_open_house, purple_line | `_build.json` written by every build |

---

## 8. Requirements for the central repo

Traceable to the findings above. The proposal (`03_proposal.md`) cites these IDs.

| ID | Requirement | Evidence |
|---|---|---|
| R1 | One canonical copy of each dataset; projects **reference** it and never copy it. | §1.2, BVA transfer, FARS copy, post 7's cross-folder dependency |
| R2 | Consumers depend on a stable dataset ID and schema, not on how the data was acquired, so the MDSP CSV can later be replaced by an API without breaking anything. | Your request; MDSP half-year batches |
| R3 | Every acquired byte records its source URL or query, retrieval time, hash and parameters, and raw data is immutable. | §1.6 |
| R4 | Explicit vintage and time-window fields everywhere, with no "current"-year columns. | AADT drift, Zillow, TIGER ×4, issue #1 |
| R5 | Fetch Maryland/DMV-scoped data and what's actually used. National data only where it's small or the analysis needs it. | §5, §1.3 |
| R6 | Shared geography backbone: boundaries per vintage, ID crosswalks, point-in-polygon assignment, custom-area aggregation with proper medians and margins of error. | §4, issue #5, planning_open_house weighting |
| R7 | Shared entity backbone for politics (people, offices, districts, contests, bills) with ID crosswalks. | §3.5, issue #6 |
| R8 | Automated quality checks at intake and at build, failing loudly. | Issues #2, #4, #5, #7, #9 |
| R9 | A standard metric library (rates, VMT exposure, inflation, ACS aggregation). | Issues #1, #8; §4 |
| R10 | Documentation that is machine-readable first, generated and validated against the data, and readable by any AI agent. | Your request; stale docs in BVA |
| R11 | Pin and freeze what's published: data packs and a chart registry. | Issue #3 |
| R12 | Secrets out of the tree; personal-data fields tagged and never published. | §5 |
| R13 | Runs locally on Windows, solo, with little upkeep; ready for cloud storage without rewriting queries. | Your constraints |
| R14 | Handles non-tabular sources: a document library (PDFs with extracted text), with LLM-extraction lineage. | §3.7, questionnaires |
| R15 | Repo hygiene: data out of git, one publishing path, environments out of OneDrive. | §5 |
