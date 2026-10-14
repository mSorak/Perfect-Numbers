# 02 — Source landscape: how to get each dataset systematically

Status: complete · Checked: 2026-10-12

**Method.** Two research passes probed endpoints directly; I then spot-checked the load-bearing claims myself. Tags:
- **[V]**: the endpoint, file or metadata was fetched today and the result is reported.
- **[B]**: believed, from documentation or search, not fetched.

No accounts were created and no forms were submitted. This document seeds the hub's source cards (`catalog/sources/*.yml`). Access modes (mirror / cache-through / live / manual) are defined in proposal §3.4.

---

## 0. Findings that change the plan

1. **Statewide crash data has no clean API.**
   - The old Maryland Open Data crash tables (`65du-s3qu`, `py4c-dicf`, `mhft-5t5y`) are retired: they return HTTP 403 **[V, re-checked by me]**. They stopped updating in May 2023.
   - The MDSP dashboards are a **Tableau Server** (`analytics.mdsp.org`, site `Public`) with guest access and data export enabled. Record-level tables are reachable only through the UI "Download → Data" flow; the internal commands return "not supported" **[V]**.
   - **Two systematic routes exist (§1):**
     - Browser automation (Playwright) of the same export you do by hand.
     - The anonymous `.csv` summary endpoint, which takes date parameters. It returns county × severity distinct-report counts, which is ideal for automatic reconciliation: for H1 2025 it shows 49,332 reports vs. 49,373 in your file (0.08% churn) **[V, re-checked by me]**.
2. **Two county crash feeds carry the same ACRS report numbers and are fully API-accessible:**
   - Montgomery County Socrata (weekly; county and local roads only). 99.8% of H1-2025 report numbers match MDSP.
   - Baltimore County ArcGIS (MDSP schema, quarterly lag, 148,088 reports). 100% match for Jan 2025.

   They make good cross-checks, and fallbacks for their counties **[V]**.
3. **The Census Data API now requires a key on every data request** (unkeyed calls redirect to `missing_key.html`) **[V, re-checked by me]**. Metadata endpoints are still open.
4. **The 2025 ACS 1-year is delayed indefinitely** by Commerce order DAO 216-26 (June 2026), which bans noise infusion in favour of coarsening and suppression **[V: 404 on the API; Census advisory says the date "is being determined"]**.
   - The 2021–25 5-year (normally December) may slip, and future vintages may carry less small-area detail **[B]**.
   - So the cache-through policy doubles as insurance. Keep every ACS slice you pull.
5. **The Population Estimates Program is files-only now.** The API stops at vintage 2021–2023, while vintage 2025 files are on www2 **[V]**.
6. **FARS 2024 (Annual Report File) is out** (2026-04-01); 2025 is not **[V]**.
   - The FARS CrashAPI moved and sits behind bot protection.
   - Bulk zips download fine **[V]**.
7. **The Maryland iMAP REST host moved** from `geodata.md.gov` (503) to `mdgeodata.md.gov` **[V]**. Your MTA bus-lines file is `MD_Transit/FeatureServer/10` there.
8. **Politics sources are better than the scraping in use today:**
   - MGA publishes `legislation.json` per session, refreshed daily: structured sponsors, subjects and dates **[V, re-checked by me: 8.2 MB, updated today]**.
   - SBE publishes clean results CSVs (`GP26_*`) **[V, re-checked by me]**, so the HTML page-scraping, and its index-as-district bug, can go.
9. **Baltimore NIBRS is an ArcGIS FeatureServer** (276,007 rows, through 2026-10-06) **[V]**. The numeric ID in your CSV filename is a per-export cache ID, not a dataset ID.

---

## 1. Crash and safety

| Dataset | Best route | Mode | Endpoint / pattern | Auth | Cadence / latency | Notes |
|---|---|---|---|---|---|---|
| **MDSP ACRS (statewide, record-level)** | **Phase 1:** manual export, then `pn intake` + automatic reconciliation. **Phase 2:** Playwright export job. | mirror (manual → automated) | Dashboard: `https://analytics.mdsp.org/t/Public/views/PublicCrash2/PublicCrash` (2024+); `…/PublicCrashData/DownloadCrashData` (2019–23). Reconciliation: `…/PublicCrash2/PublicCrash.csv?Crash%20Date%20Begin=YYYY-MM-DD&Crash%20Date%20End=YYYY-MM-DD` **[V]** | none (guest) | Data updated daily **[V]**; reports approved late → **re-pull the trailing 9 months each refresh; a month freezes at 12 months old.** Until automation: each half-year batch, export the new and the previous half-year, all entities in one session. | The logical model has more tables than the four you download: Contribs, Damage, Sequence, NMSafetyEquip **[V]**. The 2019–23 workbook offers `CrashMap.csv` with report IDs + lat/lon via URL params **[V]**. Stability medium-low: the workbook was renamed once ("PublicCrash2"). Consider asking MSP / the MDOT Highway Safety Office about a bulk extract (not verified to exist). |
| Montgomery County Crash Reporting | Socrata API | mirror (weekly incremental) | `data.montgomerycountymd.gov/resource/{bhju-22kf incidents, mmzv-x632 drivers, n7fk-dce5 non-motorists}.csv?$where=crash_date_time>='…'` **[V: 126,010 incidents, max 2026-10-07]** | app token (optional) | weekly | County and local roads only (no MSP-reported state highways); descriptive codes; preliminary |
| Baltimore County CrashData | ArcGIS MapServer | mirror (quarterly) | `bcgisapps.baltimorecountymd.gov/arcgis/rest/services/CrashData/MapServer` layer 0 reports (148,088 **[V]**), tables 2 vehicles, 4 non-motorists, 6 circumstances | none | quarterly; through 2026-06-30 | MDSP schema in upper case; native EPSG 2893 |
| MDOT SHA fatal crash locations | ArcGIS | mirror (annual) | `maps.roads.maryland.gov/arcgis/rest/services/OOTS/FatalCrash_Maryland_MDOTSHA/MapServer/0` **[V]** | none | — | 269 records, SHA roads only, with inspection findings |
| Zero Deaths MD dashboard | — | manual only | Tableau `FatalDashboards`; CSV export unusable **[V]** | — | — | Use FARS + MDSP instead |
| **FARS** (national) | Bulk zips | mirror (annual, April) | `https://static.nhtsa.gov/nhtsa/downloads/FARS/{YYYY}/National/FARS{YYYY}NationalCSV.zip` (+ `…AuxiliaryCSV.zip`) **[V: 2024 is 32.7 MB, 2026-04-01]** | none | Annual. 2024 = Annual Report File; 2023 = Final; 2024 Final arrives with the 2025 ARF (~spring 2027) **[B]** | Keep ARF and Final as separate vintages. CRSS: `…/CRSS/{YYYY}/CRSS{YYYY}CSV.zip`. API at `crashviewer.nhtsa.dot.gov/crashviewer/CrashAPI/` is browser-only (Akamai) **[V]**. |
| NHTSA crash unit costs | Seed table | manual | DOT HS 813 403 (2019, revised 2023); **no newer edition found [B]** | — | — | Keep as a versioned seed |
| USDOT VSL and BCA values | Seed table | manual | VSL **$14.2M (2025 base year)**, effective 2026-03-20 **[V]**; BCA Guidance 2026 KABCO values in 2024$: K 13.7M / A 1.30M / B 256K / C 122K / O 5.5K **[B, confirm against the PDF]** | — | annual | An alternative costing basis for E3 (KABCO maps directly onto ACRS injury codes) |
| MoCo traffic violations, camera data | Socrata | live / mirror | `4mse-ku6q` violations (2.16M rows, daily), `uv5p-zm58` speed, `3cju-6hst` red-light (quarterly totals) **[V]** | token optional | daily / quarterly | Enforcement-side context |
| Baltimore City citations (incl. speed/red-light cameras) | ArcGIS | mirror (yearly layers) | `services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/Parking_and_Moving_Citation_2026/FeatureServer/0` **[V: 817k rows]** | none | ~daily | Contains plate (`Tag`): **PII; never publish** |

**MDSP Playwright design (Phase 2):**
- Open the view with date parameters for one month.
- Select the map sheet, then Download → Data, one tab per table, "show all fields".
- Save to `raw/mdsp_acrs/<entity>/<snapshot_id>__<YYYY-MM>/` (snapshot_id in UTC).
- Reconcile against `PublicCrash.csv` for the same window (county × severity distinct counts must match within 0.5%).
- Re-run the trailing months.

**Constraints:** keep requests polite (one window at a time, off-hours), no CAPTCHA or login involved, and stop if the site's terms or behaviour change.

---

## 2. Traffic and roads

| Dataset | Best route | Mode | Endpoint | Notes |
|---|---|---|---|---|
| **MDOT SHA AADT** points (layer 0, 8,189) and segments (layer 1, 10,013) | ArcGIS FeatureServer | mirror (annual, after the ~August release) | `https://services.arcgis.com/njFNhDsUCentVYJW/ArcGIS/rest/services/MDOT_SHA_Annual_Average_Daily_Traffic/FeatureServer/{0,1}/query?where=1=1&outFields=*&outSR=4326&f=geojson&resultOffset=…&resultRecordCount=2000` **[V]** | Edited 2026-08-27. Fields AADT_2015–2024 + "AADT (Current)", ≈ **2025** (my check: the current column matches no year column). **Staging rule:** unpivot to (segment, year, aadt, aawdt, counted_or_factored), assign the current column an explicit year (if it equals exactly one `AADT_<year>`, use that year; if it matches none, use max+1 and require confirmation; record the method), and keep every annual snapshot (older years roll off: AADT_2015 is already null). Use `COUNTED_FACTORED` to separate counted values from factored ones. Avoid the stale iMAP and Socrata mirrors. |
| HPMS Maryland | FeatureServer | mirror (annual) | `https://geo.dot.gov/server/rest/services/Hosted/HPMS_FULL_MD_{YYYY}/FeatureServer/0` (2024: 190,822 sections) **[V]** | Lanes, widths, signals, AADT; roughly 2 years behind |
| SHA road inventory (centerline, functional class, posted speed signs, access control) | FeatureServer | mirror (as needed) | Same AGOL org: `MDOT_SHA_Roadway_Centerline`, `…_Posted_Speed_Limit_Signs`, etc. **[V by catalog]** | Check the item owner; the org mixes authoritative and staff layers |
| OpenStreetMap Maryland | Geofabrik PBF | mirror (per project) | `https://download.geofabrik.de/north-america/us/maryland-latest.osm.pbf` (~205 MB, daily) **[V]** | ODbL (attribution + share-alike on derived databases); Overpass for small tag pulls |
| LEHD LODES8 commute flows | Bulk CSV.gz | mirror (annual) | `https://lehd.ces.census.gov/data/lodes/LODES8/md/od/md_od_{main,aux}_JT00_{YYYY}.csv.gz` (latest 2023) **[V]** | `aux` captures out-of-state workers, which matters near DC |
| NOAA daily snow/precip | NCEI Access Data Service | cache-through | `https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=…&dataTypes=SNOW,SNWD&…&format=csv` **[V]** | No token. Silver Spring CoCoRaHS stations listed in the research notes; pair them with DCA `USW00013743` |
| MVA registrations, EVs | Socrata | mirror (monthly) | `db8v-9ewn`, `qtcv-n3tc`, `tugr-unu9` on opendata.maryland.gov **[V]** | County and ZIP level |

---

### 2b. Streets, jurisdiction and street design (Baltimore; added 2026-10-13 for the bus-lane piece)

| Dataset | Best route | Mode | Endpoint | Notes |
|---|---|---|---|---|
| Baltimore City street centerline | City ArcGIS FeatureServer | mirror | `https://baltegis.baltimorecity.gov/mapping/rest/services/Address_Points/Street_Centerline_Native/FeatureServer` (also `Road_Centerline_NG911`) **[V: in city catalog search, edited recently]** | Segment basis for bus-corridor analysis. A schema data dictionary is published alongside it. |
| Road maintenance responsibility (city vs SHA vs county) | MDOT SHA AGOL FeatureServer | mirror | `MDOT_SHA_Roadway_Maintenance_Responsibility_…` in org `njFNhDsUCentVYJW`; also `MDOT_Know_Your_Roads/FeatureServer` and HPMS layer `mdgeodata.md.gov/imap/rest/services/Transportation/MD_HighwayPerformanceMonitoringSystem/MapServer/3` **[V: catalog search]** | Core to the "who controls the street" argument; confirm field meanings before use |
| BCDOT bike facilities | City ArcGIS FeatureServer | mirror | `https://services3.arcgis.com/ZTvQ9NuONePFYofE/arcgis/rest/services/BCDOT_Bike_Facilities_Open_/FeatureServer` **[V: catalog search]** | |
| Existing bus lanes | OSM tags + hand-built seed | manual | Geofabrik MD extract (`busway=*`, `lanes:bus`, `bus:lanes`) | **No public city bus-lane layer found.** Confirm with BCDOT/MTA materials. |
| Bus service by segment | Derived from MTA GTFS (§3) | derived | GTFS `shapes.txt` + `stop_times` mapped to the street centerline | Frequency is exact from the schedule. Riders are estimated from stop boardings (iMAP `MD_Transit/9`, Summer 2024) scaled by route-month ridership. |

## 3. Transit

| Dataset | Best route | Mode | Endpoint | Notes |
|---|---|---|---|---|
| **MTA GTFS** (local bus, light rail, metro, MARC, commuter bus) | Static zips | mirror (on Last-Modified change; weekly check) | `https://feeds.mta.maryland.gov/gtfs/{local-bus,light-rail,metro,marc,commuter-bus}` → S3 **[V]** | URLs are overwritten in place, so snapshot every change. Bus, light rail and metro GTFS-RT need a Swiftly key; MARC RT and alerts are open. |
| **NTD monthly ridership** | Socrata (data.transportation.gov) | mirror (monthly) | `https://data.transportation.gov/resource/8bui-9xvu.csv?$where=state='MD'` (372,801 rows nationally, through 2026-08) **[V]** | **Official, stable cross-check** for MTA mode-level ridership (MTA = ntd_id 30034; Ride On = 30051; Circulator = 30201). Also `9ivb-8ae9` Major Safety & Security Events. |
| MTA route-level ridership | Your Power BI `querydata` connector | mirror (monthly) | `wabi-us-gov-virginia-api.analysis.usgovcloudapi.net/public/reports/querydata` (model 1525527) | Fragile and undocumented. Add a schema-drift check; also pull `route_id_gtfs`, `cx_otp` and `service_delivery`, which are in the model but not yet pulled. |
| MTA stop-level ridership | iMAP FeatureServer | mirror (as published) | `https://mdgeodata.md.gov/imap/rest/services/Transportation/MD_Transit/FeatureServer/9` (4,449 stops; Summer 2024 weekday boardings) **[V]** | |
| MTA bus lines (your `data/mta` file) | iMAP FeatureServer | mirror | `…/MD_Transit/FeatureServer/10` (128 features, identical fields) **[V]** | Prefer GTFS `shapes.txt` for geometry; keep this layer for its attributes |
| WMATA station entries | Tableau `.csv` view | mirror (monthly; history overwritten in place) | `https://exttabanalytics.wmata.com/views/RidershipDataPortal-MetroRailRidershipSummary/AvgTotalDailyEntriesbyStation.csv` (= your "Entries by Tap and noTap" file) **[V]** | Categorical URL filters work; the year filter doesn't (needs the UI) |
| WMATA GTFS | API | mirror | `api.wmata.com/gtfs/{rail,bus}-gtfs-static.zip` (free key) **[V: 401 without one]** | |
| Ride On GTFS | Static zip | mirror | `https://www.montgomerycountymd.gov/DOT-Transit/Resources/Files/GTFS/RideOnGTFS.zip` **[V]** | |
| Purple Line | — | — | Contractual revenue date Dec 30, 2027, now "dynamic"; April 2028 floated **[B: press, Oct 6 2026]**. No GTFS yet. Station and alignment layers exist in the state AGOL org **[V by name]**. | |

---

## 4. Census, boundaries and geography

| Dataset | Best route | Mode | Endpoint | Notes |
|---|---|---|---|---|
| **ACS 5-year / 1-year tables** | Census Data API (key) | **cache-through** (per dataset × vintage × table × geography) | `https://api.census.gov/data/{vintage}/acs/acs5?get=NAME,group({TABLE})&for=tract:*&in=state:24&key=…` **[V]**. Labels: `/{vintage}/acs/acs5/groups/{TABLE}.json` (no key) **[V]** | Latest: ACS5 2020–24, ACS1 2024 **[V]**. Block groups need `in=state:24 county:*`. Store E and M together. Write a ~100-line wrapper; use `censusdis` for interactive discovery. |
| NHGIS (time series, historical decennial, crosswalks) | IPUMS API (key) | cache-through (extract definition hashed; zip kept) | `https://api.ipums.org/extracts?collection=nhgis&version=2`; `geographicExtents: ["240"]` **[V spec]** | Use for standardized time series (2010→2020 tracts), pre-2000 data and crosswalks (`nhgis_tr2010_tr2020_24.zip`, key required). Extracts expire after ~72 h, so download and keep them. **Merge the two existing clients.** |
| 2020 Decennial (DHC, PL) | Census API | cache-through (freeze) | `2020/dec/dhc`, `2020/dec/pl` **[V catalog]** | Static |
| PEP population and housing units | www2 files | mirror (per vintage; keep all vintages) | `https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv`; sub-county `…/cities/totals/sub-est2025_24.csv`; housing units `…/tables/2020-2025/housing/totals/CO-EST2025-HU-24.xlsx` **[V]** | Each vintage re-estimates back to 2020: never mix vintages |
| Building Permits Survey | www2 files | mirror (monthly; annual is final) | `https://www2.census.gov/econ/bps/County/co{YY}{MM}c.txt`, `co{YYYY}a.txt`; Place South region `so…`; compiled `Master%20Data%20Set/BPS_Compiled_File_{YYYYMM}.zip` **[V]** | Two-row header |
| Planning Database (tract / block group) | Census API | cache-through | `{2025,2026}/pdb/{tract,blockgroup}` **[V catalog]** | Handy for land area, density and hard-to-count measures |
| Gazetteer (land area, internal points) | www2 | mirror (per vintage) | `…/gazetteer/{YYYY}_Gazetteer/{YYYY}_Gaz_{tracts,counties,place,…}_national.zip` (2026 posted 2026-09-09) **[V]** | Correct land-area source for density, instead of computing areas from polygons |
| **TIGER/Line state files** | www2 | mirror (per vintage) | Per-state: `https://www2.census.gov/geo/tiger/TIGER{YYYY}/{TRACT,BG,PLACE,…}/tl_{YYYY}_{24,11,51}_{layer}.zip` (MD tract 2024 = 5.8 MB) **[V]**. **County and ZCTA are national-only** (`COUNTY/tl_{YYYY}_us_county.zip`, ~84 MB; `ZCTA520/…_us_zcta520.zip`): download once per vintage, filter at intake, and record the national file's URL and hash; cartographic `GENZ{YYYY}/shp/cb_{YYYY}_24_tract_500k.zip` **[V]** | **TIGER2026 was posted 2026-10-06** **[V]**. `pygris` 0.2.1 wraps these URLs. Replaces ~9.5 GB of national files. |
| Point → tract lookups | **Local** point-in-polygon (DuckDB spatial or geopandas) | — | Census Geocoder coordinate lookups are one point per request **[V]** | Use for ad hoc checks only |
| MD legislative / congressional districts (2022), precincts 2026 | iMAP FeatureServer | mirror (per plan) | `https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_ElectionBoundaries/FeatureServer/{0,1,2}` **[V]** | Socrata `yvef-set5` also carries the current senator and delegates per district, with Maryland Manual URLs **[V]** |
| County council districts | MoCo Socrata `5xdu-htbh` **[V]**; Baltimore City `dgtc-48ik` **[V]**; Howard: **not found** (check its GIS hub manually) | mirror | | |
| Parcels / assessments | Socrata `ed4q-f8tm` (2.43M rows, 221 columns; owner names hidden) **[V]**; iMAP `PlanningCadastre/MD_Property*` | mirror (as needed) | | Large: pull only by county |

---

## 5. Housing and economy

| Dataset | Best route | Mode | Endpoint | Notes |
|---|---|---|---|---|
| **Zillow ZHVI / ZORI** | CDN CSV | mirror (monthly; **keep every pull**, since history is re-smoothed) | `https://files.zillowstatic.com/research/public_csvs/{zhvi,zori}/{State,Metro,County,City,Zip,Neighborhood}_{metric}_{options}.csv` (through 2026-08) **[V]** | No API. **Attribution to Zillow required**; redistribution not addressed, so treat as `attribution_required`, and as not allowed in public packs until checked. |
| FHFA HPI | Master CSV + annual developmental xlsx | mirror | `https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv`; `…/annual/hpi_at_{county,tract,…}.xlsx` **[V]** | Revised every release. Many series are also on FRED. |
| Redfin | S3 CSV | mirror | `redfin-public-data.s3.us-west-2.amazonaws.com/redfin_data_center/{topic}/{monthly,weekly}/{all_counties,…}.csv` **[V]** | **The old `redfin_market_tracker` files are frozen** (since 2026-06-02) |
| Apartment List rents | Scrape asset URLs from the page JSON | mirror | `assets.ctfassets.net/…/Apartment_List_Rent_Estimates_YYYY_MM.csv` **[V]** | URLs are hashed, not predictable |
| HUD FMR / Income limits / CHAS / USPS ZIP crosswalk | HUD API (token) | cache-through | `https://www.huduser.gov/hudapi/public/{fmr,il,chas,usps}/…` **[V: 401 without token]** | The website and bulk files block scripts (202 with an empty body) **[V]** |
| MD Planning (projections, sales) | xlsx files | mirror (snapshot; overwritten in place) | `planning.maryland.gov/MSDC/Documents/popproj/TotalPopProj.xlsx` etc. **[V]** | |
| MD permits, foreclosures | Socrata | mirror | `c7z9-v9mr`, `w3bc-8mnv`, `ftsr-vapt` **[V]** | |
| MoCo permits | Socrata | mirror | `m88u-pqki` residential, `i26v-w6bd` commercial **[V]** | Relevant to the "multifamily permit collapse" claim in post 7 |
| Harvard JCHS | Manual | manual | — | Snapshot the appendix xlsx; record the interactive-map provenance |
| **CPI-U** (for all dollar adjustments) | BLS API v2 (key) | cache-through | `POST https://api.bls.gov/publicAPI/v2/timeseries/data/`, series **`CUUR0000SA0`** (Aug 2026 = 334.980; 2025 annual avg = 321.943) **[V]**; Baltimore-area `CUURS35ESA0` | NSA CPI-U is never revised, so use it for dollar conversion. Pin the target period (e.g. 2025 annual average) and print it in chart notes. |
| LAUS county unemployment | BLS API v2 | cache-through | `LAUCN{SS}{CCC}00000000{03,04,05,06}` (MoCo rate = `LAUCN240310000000003`) **[V]** | Revised each March, so re-pull five years every spring. **Never mix with seasonally adjusted state/US series** without labeling. |
| FRED / ALFRED | FRED API (key) | cache-through | `api.stlouisfed.org/fred/series/observations?series_id=…&api_key=…` (+ `realtime_start` for vintages); v2 release bulk **[V]** | Keyless `fredgraph.csv?id=` works for prototyping **[V]** |
| BEA county income / GDP | Bulk zip or API | mirror (annual) | `https://apps.bea.gov/regional/zip/CAINC1.zip` (through 2024) **[V]** | Comprehensive revisions: keep each zip |
| QCEW | Open-data CSV slices | mirror (quarterly) | `https://data.bls.gov/cew/data/api/{YYYY}/{Q|a}/area/{FIPS}.csv` (latest 2026Q1) **[V]** | |

---

## 6. Crime

| Dataset | Best route | Mode | Endpoint | Notes |
|---|---|---|---|---|
| **Baltimore NIBRS Group A** | ArcGIS FeatureServer | mirror (weekly 90-day re-pull + quarterly full pull) | `https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/NIBRS_GroupA_Crime_Data/FeatureServer/0` (276,007 rows, 2022-01-01 → 2026-10-06) **[V]** | Hub item `204beefe92a645d79fdf0969957bbdf8`. Timestamps are UTC. Records get reclassified. Victim fields are PII. Never mix with legacy SRS Part 1 (frozen 2024-12) without a mapping. |
| MoCo crime | Socrata | mirror | `icn6-v9z3` (511k rows, daily) **[V]** | |
| Prince George's crime | Socrata | mirror | `xjru-idbe` (Jul 2023→) **[V]** | |
| Statewide / agency series | FBI Crime Data Explorer API (api.data.gov key) | cache-through (snapshot responses) | `https://api.usa.gov/crime/fbi/cde/summarized/agency/{ORI}/{offense}?from=MM-YYYY&to=MM-YYYY` **[V]** | **The last ~3 months are incomplete:** the BPD Jul–Sep 2026 counts were 453, 179 and 5. Mask or flag them. |
| Gun Violence Archive | — | manual, cited only | — | Proprietary terms **[B]** |

---

## 7. Politics and legislature

| Dataset | Best route | Mode | Endpoint | Notes |
|---|---|---|---|---|
| **MGA bills** | `legislation.json` | mirror (daily in session, weekly otherwise; **keep daily snapshots in session**, since status is overwritten) | `https://mgaleg.maryland.gov/{yyyy}rs/misc/billsmasterlist/legislation.json` **[V, re-checked by me]** | Structured sponsors, subjects and dates. Keep the CSV as a fallback. Bill PDFs, fiscal notes and roll-call PDFs follow stable paths. |
| Roll-call votes | LegiScan weekly datasets (key; CC BY 4.0) **[B terms]**, or Open States API v3 (key) | mirror (weekly) | `api.legiscan.com/?key=…&op=getDataset&state=MD` | MGA votes are PDFs only |
| Legislator roster | Open States CSV + `openstates/people` YAML (CC0) | mirror | `https://data.openstates.org/people/current/md.csv` (188 members) **[V]** | ocd-person IDs are the person spine. Cross-check against `yvef-set5`. |
| **SBE results** | CSV files | mirror (freeze at certification; **snapshot repeatedly during the GG26 canvass**) | `https://elections.maryland.gov/elections/2026/election_data/GP26_{AllPrecincts,LegislativeBreakDown,…}{Party}.csv` **[V, re-checked by me]**; past cycles under `/elections/archive/{YYYY}/election_data/` | **Soft-404s:** unknown paths return HTML with HTTP 200, so check the content type. SBE county codes (01–24, alphabetical) ≠ FIPS. General-election files aren't split by party. |
| SBE candidate lists | CSV files | mirror (until certification) | `…/2026/general_candidates/2026_GG_{statewide,all_counties,houseofdelegatesbydistrict,…}_candidatelist.csv` (updated 2026-10-12) **[V]** | |
| Voter registration | Monthly PDFs | manual / PDF extraction | `/pdf/vrar/{YYYY}/MSR-{YYYY}_{MM}.pdf` **[V]** | |
| MoCo Council bills and resolutions | Socrata | mirror | `ksj8-bd3u` bills (with votes), `imr8-iedu` resolutions **[V]** | MoCo's Legistar instance is dead (2023) |
| Baltimore City / Prince George's council | Legistar Web API | mirror | `https://webapi.legistar.com/v1/{baltimore,princegeorgescountymd}/matters` **[V]** | |
| Howard County council | — | manual | none found | |
| Campaign finance (state) | MD-CRIS public UI | manual (snapshot exports) | relaunched 2026-01-12; no bulk API **[B]** | |
| Campaign finance (federal) | FEC API (api.data.gov key) | cache-through | `api.open.fec.gov/v1/…` **[V]** | |
| Historical results (pre-2022) | OpenElections MD | mirror (once) | `openelections-results-md` (2000–2020) **[V]** | |

---

## 8. Keys to obtain (all free)

| Service | Key | Status |
|---|---|---|
| Census Data API | key | **required**, *you'll need one* |
| IPUMS | key | have one; **rotate it** |
| BLS v2 | registration key | — |
| FRED | key | — |
| BEA | UserID | — |
| api.data.gov | key | covers the FBI CDE and FEC APIs |
| HUD USER | token | — |
| Open States v3 | key | — |
| LegiScan | key | — |
| WMATA | developer key | — |
| Socrata | app token(s) | optional |

All of them go in `%USERPROFILE%\.config\pn\.env`.

---

## 9. Summary: what changes vs. today

| Today | Replace with | Phase |
|---|---|---|
| MDSP half-year manual exports, unchecked | Monthly-window exports (manual → Playwright) + automatic reconciliation against the `.csv` count endpoint + MoCo/BaCo cross-checks | 1 (manual + reconcile) → 2 (automate) |
| National NHGIS shapefiles ×4 | TIGER state files per vintage for tract/BG/place (MD; DC/VA when needed); national county file filtered once per vintage | 1 |
| Hand-made NHGIS extracts per project | `census.acs5` cache-through via the Census API; one IPUMS client for NHGIS-only products | 1 |
| Excel density workbooks | Gazetteer land area + ACS/DHC population → `census` marts with national percentiles | 1–2 |
| AADT Hub downloads ×3 | FeatureServer annual snapshots, unpivoted with explicit years | 2 |
| FARS re-extraction in place | Bulk zips → Parquet by year; add 2024 ARF | 2 |
| Hard-coded CPI factor 1.26 | `econ.cpi_u` from BLS (CUUR0000SA0) + `to_real_dollars()` | 1 |
| FRED manual CSVs with renamed columns | BLS/FRED API with series IDs kept | 2 |
| Zillow undated copies | Dated monthly CDN pulls | 2 |
| MTA Power BI pulls (one-off) | Wrapped connector + drift check; NTD `8bui-9xvu` as official cross-check; GTFS | 2 |
| SBE HTML scraping | `GP26_*` / `GG26_*` CSVs, snapshotted | 2 (or 1, if election-night coverage) |
| MGA BillMasterList.csv | `legislation.json` daily snapshots in session | 2 |
| Baltimore NIBRS manual export | FeatureServer mirror with UTC → local conversion | 2 |
| MTA bus-lines Hub download | GTFS shapes (+ iMAP layer 10 attributes) | 2 |
| WMATA manual Tableau export | `.csv` view URL, monthly snapshot | 2 |
