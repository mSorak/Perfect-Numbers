# `transit.ntd_monthly` — NTD monthly ridership and service, Maryland agencies

FTA National Transit Database complete monthly ridership (with adjustments and estimates) for Maryland reporters: unlinked trips, revenue miles and hours, by agency × mode × type of service.

- **Grain:** one row per agency × mode × type of service × month
- **Primary key:** ntd_id, mode, type_of_service, month
- **Layer / access mode:** staging / mirror
- **Source:** fta_ntd
- **Depends on:** raw:fta_ntd/monthly_ridership_md
- **Card:** `catalog/datasets/transit/ntd_monthly.yml`
- **Current build:** 20261014T0147Z · 7,321 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'fta_ntd/monthly_ridership_md': '20261014T0137Z'}}
- **Coverage:** 2002-01-01 → 2026-08-01

## Columns

| Column | Type | Description |
|---|---|---|
| `ntd_id` | varchar | NTD agency ID (MTA = 30034). |
| `agency` | varchar | Agency name. |
| `mode` | varchar | NTD mode code (MB bus, LR, HR, CR, CB, DR, …). |
| `type_of_service` | varchar | DO directly operated, PT purchased transportation. |
| `mode_group` | varchar | Bus / Rail / Other. |
| `month` | date | First day of month. |
| `unlinked_trips` | bigint | Unlinked passenger trips (UPT). |
| `vehicle_revenue_miles` | bigint | Vehicle revenue miles (VRM). |
| `vehicle_revenue_hours` | bigint | Vehicle revenue hours (VRH). |
| `vehicles_operated_max` | integer | Vehicles operated in maximum service (VOMS). |
| `uza_name` | varchar | Urbanized area. |
| `state` | varchar | State. |

## License and citation

```yaml
terms: public domain
redistribution: allowed
citation: FTA National Transit Database, Complete Monthly Ridership (8bui-9xvu), retrieved
  {retrieved_at}
```
