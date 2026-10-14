# `crash.acrs_person` — People in Maryland crash reports (ACRS occupants and non-motorists), 2024 onward

One row per person on an ACRS crash report: vehicle occupants (drivers and passengers) and non-motorists (pedestrians, cyclists, …), newest monthly pull of each month. injury_code is the KABCO-based ACRS injury status ('01' fatal … '05' no apparent injury); map to cost levels with ref.acrs_injury_to_mais.

- **Grain:** one row per report × person
- **Primary key:** report_number, person_id, person_role
- **Layer / access mode:** staging / mirror
- **Source:** mdsp_acrs
- **Depends on:** raw:mdsp_acrs/occupants, raw:mdsp_acrs/nonmotorists, crash.acrs_report
- **Card:** `catalog/datasets/crash/acrs_person.yml`
- **Current build:** 20261014T210157Z · 651,048 rows · git c2a0ea2
- **Inputs:** {'datasets': {'crash.acrs_report': '20261014T210156Z'}, 'raw': {'mdsp_acrs/occupants': ['20261014T1954Z__2024-01', '20261014T1955Z__2024-02', '20261014T1956Z__2024-03', '20261014T1957Z__2024-04', '20261014T1959Z__2024-05', '20261014T2000Z__2024-06', '20261014T2001Z__2024-07', '20261014T2002Z__2024-08', '20261014T2003Z__2024-09', '20261014T2005Z__2024-10', '20261014T2006Z__2024-11', '20261014T2007Z__2024-12', '20261014T2034Z__2025-01', '20261014T2009Z__2025-02', '20261014T2010Z__2025-03', '20261014T2012Z__2025-04', '20261014T2013Z__2025-05', '20261014T2014Z__2025-06', '20261014T2015Z__2025-07', '20261014T2016Z__2025-08', '20261014T1951Z__2025-09', '20261014T2018Z__2025-10', '20261014T2019Z__2025-11', '20261014T2021Z__2025-12', '20261014T2022Z__2026-01', '20261014T2023Z__2026-02', '20261014T2024Z__2026-03', '20261014T2025Z__2026-04', '20261014T2026Z__2026-05', '20261014T2027Z__2026-06', '20261014T2028Z__2026-07', '20261014T2030Z__2026-08', '20261014T2031Z__2026-09'], 'mdsp_acrs/nonmotorists': ['20261014T1954Z__2024-01', '20261014T1955Z__2024-02', '20261014T1956Z__2024-03', '20261014T1957Z__2024-04', '20261014T1959Z__2024-05', '20261014T2000Z__2024-06', '20261014T2001Z__2024-07', '20261014T2002Z__2024-08', '20261014T2003Z__2024-09', '20261014T2005Z__2024-10', '20261014T2006Z__2024-11', '20261014T2007Z__2024-12', '20261014T2034Z__2025-01', '20261014T2009Z__2025-02', '20261014T2010Z__2025-03', '20261014T2012Z__2025-04', '20261014T2013Z__2025-05', '20261014T2014Z__2025-06', '20261014T2015Z__2025-07', '20261014T2016Z__2025-08', '20261014T1951Z__2025-09', '20261014T2018Z__2025-10', '20261014T2019Z__2025-11', '20261014T2021Z__2025-12', '20261014T2022Z__2026-01', '20261014T2023Z__2026-02', '20261014T2024Z__2026-03', '20261014T2025Z__2026-04', '20261014T2026Z__2026-05', '20261014T2027Z__2026-06', '20261014T2028Z__2026-07', '20261014T2030Z__2026-08', '20261014T2031Z__2026-09']}}

## Columns

| Column | Type | Description |
|---|---|---|
| `report_number` | varchar | ACRS report number. |
| `person_id` | varchar | ACRS person GUID. |
| `person_role` | varchar | occupant or nonmotorist. |
| `person_type` | varchar | Occupant type (driver, passenger, …) or non-motorist type (pedestrian, cyclist, …). |
| `vehicle_id` | varchar | Occupant's vehicle, or the vehicle that struck the non-motorist. |
| `injury_code` | varchar | ACRS injury status code '01'–'05'; null if not recorded. |
| `injury_status` | varchar | Injury status label. |
| `age` | integer | Age in years. |
| `sex` | varchar | Sex as recorded. |
| `restraint` | varchar | Restraint use (occupants). |
| `seating_location` | varchar | Seating position (occupants) or location (non-motorists). |
| `ejection` | varchar | Ejection (occupants). |
| `source_period` | varchar | Snapshot period. |
| `source_snapshot_id` | varchar | Raw snapshot this row came from. |

## Parameters

```yaml
snapshot_grain: month
```

## Caveats

- 2026-10-14: Some persons have no injury status (about 7% of occupants). The published cost model (method 2026.1) costs them at zero.
- 2026-10-14: age and sex are personal data (pii): aggregate only; never publish person-level rows. Name, address, zip, licence and test-result fields are not staged.

## License and citation

```yaml
terms: MDSP public dashboard data; no explicit license
redistribution: attribution
citation: Maryland State Police, ACRS crash data (public dashboard), retrieved {retrieved_at}
```
