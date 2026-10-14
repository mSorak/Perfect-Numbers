# Conventions

Rules every dataset follows. They're enforced by `pn check` where possible, and by review otherwise. Full rationale: `docs/design/03_proposal.md` §5.3 and §8.

## Identifiers and files
- **Dataset ID:** `<domain>.<dataset>`, a singular noun, snake_case (`transit.gtfs_stop`, not `stops_2026`). It is also the DuckDB view name.
- **Card:** `catalog/datasets/<domain>/<dataset>.yml`. **Source card:** `catalog/sources/<source_id>.yml`. Cadence lives only in the source card.
- **Build logic:** `pipelines/<domain>/<dataset>.sql`, or a Python function `pipelines/<domain>/<file>.py:<func>` that returns SQL or a DataFrame.
- **Raw snapshots:** `$PN_DATA_ROOT/raw/<source>/<entity>/<snapshot_id>/`, where `snapshot_id` is UTC `YYYYMMDDTHHMMZ`. Raw files are immutable and read-only. Files whose names start with `_` are request/response metadata and don't count toward change detection.
- **Builds:** `$PN_DATA_ROOT/<staging|marts>/<domain>/<dataset>/build=<YYYYMMDDTHHMMSSZ>.parquet`, plus `_current.json`. The last 5 builds are kept.

## Columns
- snake_case. Booleans `is_*`, `has_*`, `on_*`. Counts `n_*`. Money `*_usd<year>`. Rates `*_per_<n>` or `*_per_hour`.
- **Every mart column is documented** in its card (`pn check` errors otherwise). Staging gets a warning only.
- Keep source codes and add labels; never collapse codes into binaries in staging. Codes whose meaning isn't confirmed get a caveat (e.g. `traffic.street_segment.subtype_code`).
- Sentinel and blank values become NULL.

## Keys
- Census geography: `geoid` (zero-padded text) plus `geoid_vintage`. County `24510` = Baltimore city, `24005` = Baltimore County.
- **MDOT county codes are alphabetical, not FIPS** (Baltimore City = 24, Baltimore County = 3). Always convert to `county_geoid`.
- Transit: GTFS `route_id`, `trip_id`, `stop_id`, `shape_id` as text. The CX dashboard's `route_id` joins to GTFS through `transit.mta_route.route_id_gtfs`.
- Crashes (Phase 2): `report_number` (ACRS, upper-case, trimmed). FARS: `(fars_year, st_case)`.

## Time
- `date`, `month` (first of month), `year` for what a row describes. `vintage` or `*_snapshot_id` for the edition. Never a "current" column.
- Timestamps are stored in UTC, with the local zone documented. GTFS times are seconds after service-day midnight and can exceed 86,400.
- Any rate carries its window explicitly (annual vs multi-year). Numerator and denominator cover the same period.

## Geometry
- **Store** as `OGC:CRS84` (lon/lat), written as GeoParquet by DuckDB. NAD83 sources are relabelled, not transformed (under 2 m).
- **Measure** in `EPSG:26985` (NAD83 / Maryland, metres): `ST_Transform(geometry, 'OGC:CRS84', 'EPSG:26985')`. Every session sets `geometry_always_xy = true`.
- Land area comes from Census `aland_m2`. TIGER polygons include water, so polygon area ≠ land area.
- `*_display` geometry (simplified) is for maps only.
- **Line-to-street matching** uses `pndata.geo.match_lines_to_segments`. It requires both overlap (share within a buffer) and alignment (bearing), so cross streets don't match.

## Tests every card should have
Primary key unique and not null; relationships to parent tables (warning level when history legitimately contains retired keys); accepted values for codes; and at least one **domain sanity check** that would catch a plausible failure (area ratio, total length, buses per hour, row-count band).

## Scope
Maryland/Baltimore by default. Download national files only when no per-state file exists (TIGER county and ZCTA), then filter at staging.
