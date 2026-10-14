# `crash.acrs_vehicle` — Vehicles in Maryland crash reports (ACRS, MDSP), 2024 onward

One row per vehicle (unit) on an ACRS crash report, newest monthly pull of each month. Join to crash.acrs_report on report_number. VIN, plate-adjacent and carrier fields stay in raw only.

- **Grain:** one row per report × vehicle
- **Primary key:** report_number, vehicle_id
- **Layer / access mode:** staging / mirror
- **Source:** mdsp_acrs
- **Depends on:** raw:mdsp_acrs/vehicles, crash.acrs_report
- **Card:** `catalog/datasets/crash/acrs_vehicle.yml`
- **Current build:** 20261014T210159Z · 533,685 rows · git c2a0ea2
- **Inputs:** {'datasets': {'crash.acrs_report': '20261014T210156Z'}, 'raw': {'mdsp_acrs/vehicles': ['20261014T1954Z__2024-01', '20261014T1955Z__2024-02', '20261014T1956Z__2024-03', '20261014T1957Z__2024-04', '20261014T1959Z__2024-05', '20261014T2000Z__2024-06', '20261014T2001Z__2024-07', '20261014T2002Z__2024-08', '20261014T2003Z__2024-09', '20261014T2005Z__2024-10', '20261014T2006Z__2024-11', '20261014T2007Z__2024-12', '20261014T2034Z__2025-01', '20261014T2009Z__2025-02', '20261014T2010Z__2025-03', '20261014T2012Z__2025-04', '20261014T2013Z__2025-05', '20261014T2014Z__2025-06', '20261014T2015Z__2025-07', '20261014T2016Z__2025-08', '20261014T1951Z__2025-09', '20261014T2018Z__2025-10', '20261014T2019Z__2025-11', '20261014T2021Z__2025-12', '20261014T2022Z__2026-01', '20261014T2023Z__2026-02', '20261014T2024Z__2026-03', '20261014T2025Z__2026-04', '20261014T2026Z__2026-05', '20261014T2027Z__2026-06', '20261014T2028Z__2026-07', '20261014T2030Z__2026-08', '20261014T2031Z__2026-09']}}

## Columns

| Column | Type | Description |
|---|---|---|
| `report_number` | varchar | ACRS report number. |
| `vehicle_id` | varchar | ACRS vehicle GUID. |
| `unit_number` | integer | Unit number on the report. |
| `body_type_code` | varchar | Body type code. |
| `body_type` | varchar | Body type. |
| `large_vehicle_body_type` | varchar | Large-vehicle body type, if any. |
| `make` | varchar | Make. |
| `model` | varchar | Model. |
| `model_year` | integer | Model year. |
| `movement` | varchar | Vehicle movement before crash. |
| `travel_direction` | varchar | Direction of travel. |
| `first_impact` | varchar | Point of first impact. |
| `most_harmful_event` | varchar | Most harmful event for this vehicle. |
| `damage_extent` | varchar | Extent of damage. |
| `special_function` | varchar | Special function (transit bus, police, …). |
| `emergency_use` | varchar | Emergency use. |
| `speed_limit_mph` | integer | Posted speed limit (mph). |
| `through_lanes` | integer | Number of through lanes. |
| `left_scene` | varchar | Hit-and-run / left scene flag as published. |
| `is_parked_raw` | varchar | Parked flag as published (not yet normalised). |
| `source_period` | varchar | Snapshot period. |
| `source_snapshot_id` | varchar | Raw snapshot this row came from. |

## Parameters

```yaml
snapshot_grain: month
```

## Caveats

- 2026-10-14: VIN Veh is deliberately not staged (it identifies a vehicle). It remains in raw for verified needs only.

## License and citation

```yaml
terms: MDSP public dashboard data; no explicit license
redistribution: attribution
citation: Maryland State Police, ACRS crash data (public dashboard), retrieved {retrieved_at}
```
