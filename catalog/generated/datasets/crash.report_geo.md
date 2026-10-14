# `crash.report_geo` — Census geography of each Maryland crash report (point in polygon, TIGER 2024)

County and census tract (2024 TIGER/Line boundaries) containing each crash's coordinates. This is the geography the published crash-cost summaries use; it can differ from ACRS 'Crash County' (crash.acrs_report.county_geoid) near borders and where the officer's county differs from the point. Join to crash.report_cost on report_number.

- **Grain:** one row per crash report
- **Primary key:** report_number
- **Layer / access mode:** staging / derived
- **Source:** derived
- **Depends on:** crash.acrs_report, geo.county, geo.tract
- **Card:** `catalog/datasets/crash/report_geo.yml`
- **Current build:** 20261014T210557Z · 287,019 rows · git c2a0ea2
- **Inputs:** {'datasets': {'crash.acrs_report': '20261014T210156Z', 'geo.county': '20261014T0143Z', 'geo.tract': '20261014T0143Z'}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `report_number` | varchar | ACRS report number. |
| `county_geoid` | varchar | County containing the crash point (TIGER 2024); null if none. |
| `tract_geoid` | varchar | Census tract containing the crash point (TIGER 2024); null if none. |
| `geoid_vintage` | integer | Boundary vintage (2024). |
| `acrs_county_geoid` | varchar | County from ACRS Crash County, for comparison. |
| `county_differs_from_acrs` | boolean | True when the point-in-polygon county differs from ACRS Crash County (or is null). |
| `has_point` | boolean | True if the report has usable coordinates. |

## Caveats

- 2026-10-14: TIGER polygons include water, so crashes on bridges, tunnels and harbor crossings get a county and tract. The published crash-cost summaries used shoreline-clipped NHGIS shapes and left those unassigned (461 reports, $194.8M in 2024–2025); everywhere else the two agree (tests/test_crash_parity.py). Points outside every Maryland polygon get null.
- 2026-10-14: Points exactly on a boundary are assigned with 'intersects', ties to the lowest GEOID.
- 2026-10-14: Places (municipalities/CDPs) are not yet included; the published place summaries need TIGER place polygons (geo.place, not yet built).

## License and citation

```yaml
terms: derived from MDSP ACRS and Census TIGER/Line
redistribution: attribution
```
