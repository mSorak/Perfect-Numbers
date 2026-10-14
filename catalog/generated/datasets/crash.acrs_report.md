# `crash.acrs_report` — Maryland crash reports (ACRS, MDSP), 2024 onward

One row per police crash report in Maryland's Automated Crash Reporting System, as exported by MDSP's public dashboard, with the newest monthly pull of each month. Persons: crash.acrs_person; vehicles: crash.acrs_vehicle; costs: crash.report_cost. All 72 source columns remain in raw/mdsp_acrs; staging keeps the ones analyses use.

- **Grain:** one row per crash report
- **Primary key:** report_number
- **Layer / access mode:** staging / mirror
- **Source:** mdsp_acrs
- **Depends on:** raw:mdsp_acrs/reports, ref.county_codes
- **Card:** `catalog/datasets/crash/acrs_report.yml`
- **Current build:** 20261014T210156Z · 287,019 rows · git c2a0ea2
- **Inputs:** {'datasets': {'ref.county_codes': '20261014T210156Z'}, 'raw': {'mdsp_acrs/reports': ['20261014T1954Z__2024-01', '20261014T1955Z__2024-02', '20261014T1956Z__2024-03', '20261014T1957Z__2024-04', '20261014T1959Z__2024-05', '20261014T2000Z__2024-06', '20261014T2001Z__2024-07', '20261014T2002Z__2024-08', '20261014T2003Z__2024-09', '20261014T2005Z__2024-10', '20261014T2006Z__2024-11', '20261014T2007Z__2024-12', '20261014T2034Z__2025-01', '20261014T2009Z__2025-02', '20261014T2010Z__2025-03', '20261014T2012Z__2025-04', '20261014T2013Z__2025-05', '20261014T2014Z__2025-06', '20261014T2015Z__2025-07', '20261014T2016Z__2025-08', '20261014T1951Z__2025-09', '20261014T2018Z__2025-10', '20261014T2019Z__2025-11', '20261014T2021Z__2025-12', '20261014T2022Z__2026-01', '20261014T2023Z__2026-02', '20261014T2024Z__2026-03', '20261014T2025Z__2026-04', '20261014T2026Z__2026-05', '20261014T2027Z__2026-06', '20261014T2028Z__2026-07', '20261014T2030Z__2026-08', '20261014T2031Z__2026-09']}}
- **Coverage:** 2024-01-01 → 2026-09-30

## Columns

| Column | Type | Description |
|---|---|---|
| `report_number` | varchar | ACRS report number, upper-case, trimmed. |
| `crash_date` | date | Crash date (Crashdate). |
| `crash_year` | bigint | Calendar year of crash_date. |
| `crash_time` | varchar | Crash time HH:MM, local. |
| `crash_hour` | integer | Hour 0–23. |
| `day_of_week` | varchar | Day of week as published. |
| `county_geoid` | varchar | County FIPS via ref.county_codes. |
| `acrs_county_code` | varchar | ACRS county code ('01'–'24', alphabetical, not FIPS). |
| `acrs_county_name` | varchar | ACRS county name. |
| `severity_code` | integer | 1 fatal, 2 injury, 3 property damage only. |
| `severity` | varchar | Severity label. |
| `agency_code` | varchar | Reporting agency code. |
| `agency_name` | varchar | Reporting agency. |
| `road_name` | varchar | Road name. |
| `route_number` | varchar | Route number. |
| `route_type_code` | varchar | Route type code. |
| `route_type` | varchar | Route type (Interstate, US, Maryland, County, Municipality, …). |
| `intersecting_road_name` | varchar | Cross street, if any. |
| `road_id` | varchar | Road ID as published. |
| `milepoint` | double | Milepoint distance. |
| `milepoint_direction` | varchar | Milepoint direction. |
| `functional_class_code` | varchar | Functional class code. |
| `functional_class` | varchar | Functional class. |
| `collision_type_code` | varchar | Collision impact code. |
| `collision_type` | varchar | Collision impact (rear end, angle, …). |
| `first_harm_event_code` | varchar | First harmful event code. |
| `first_harm_event` | varchar | First harmful event. |
| `light` | varchar | Light condition. |
| `surface` | varchar | Road surface condition. |
| `junction` | varchar | Junction relation. |
| `is_impaired` | boolean | Impaired-driving crash flag. |
| `is_motorcycle` | boolean | Motorcycle involved. |
| `is_nonmotorist` | boolean | Pedestrian/cyclist/other non-motorist involved. |
| `is_large_vehicle` | boolean | Large vehicle involved. |
| `is_work_zone` | boolean | Work-zone related. |
| `has_unrestrained_occupant` | boolean | Any unrestrained occupant. |
| `latitude` | double | Latitude as published. |
| `longitude` | double | Longitude as published. |
| `geometry` | geometry | Crash point, OGC:CRS84; null if coordinates fall outside Maryland's bounding box. |
| `source_period` | varchar | Snapshot period (YYYY-MM, or YYYYH1/H2 for legacy). |
| `source_snapshot_id` | varchar | Raw snapshot this row came from. |

## Parameters

```yaml
snapshot_grain: month
```

## Caveats

- 2026-10-14: Reports are revised and occasionally withdrawn after approval. Counts for recent months grow for several months; each monthly refresh re-pulls the trailing 9 months.
- 2026-10-14: 2024–2025 has 210,838 reports in the 2026-10 monthly pulls vs 210,860 in the legacy half-year exports used by the published crash-cost model (2026-03/06). Use snapshot_grain half_year only to reproduce that model.
- 2026-10-14: County is ACRS 'Crash County' (where the officer placed the crash), joined via ref.county_codes. A point-in-polygon county can differ near borders; see crash.report_cost for the spatial version once built.

## License and citation

```yaml
terms: MDSP public dashboard data; no explicit license
redistribution: attribution
citation: Maryland State Police, ACRS crash data (public dashboard), retrieved {retrieved_at}
```
