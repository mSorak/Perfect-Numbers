# `transit.mta_ridership_route_month` — MTA ridership by route and month (CX dashboard)

Monthly unlinked trips and average daily, weekday and weekend riders per route, from the MTA Customer Experience dashboard data model.

- **Grain:** one row per route × mode × month
- **Primary key:** route_id, mode_id, month
- **Layer / access mode:** staging / mirror
- **Source:** mta_cx_powerbi
- **Depends on:** raw:mta_cx_powerbi/route_ridership, transit.mta_route
- **Card:** `catalog/datasets/transit/mta_ridership_route_month.yml`
- **Current build:** 20261014T020043Z · 12,307 rows · git d8c1e6e
- **Inputs:** {'datasets': {'transit.mta_route': '20261014T020043Z'}, 'raw': {'mta_cx_powerbi/route_ridership': '20261014T0138Z'}}
- **Coverage:** 2011-07-01 → 2026-09-01

## Columns

| Column | Type | Description |
|---|---|---|
| `route_id` | varchar | CX route ID (transit.mta_route). UNASSIGNED = ridership the dashboard does not attribute to a route (kept so mode totals add up). |
| `mode_id` | bigint | CX mode ID. |
| `month` | date | First day of month. |
| `riders` | double | Total unlinked trips in the month. |
| `average_daily_riders` | double | Average daily riders. |
| `average_weekday_riders` | double | Average weekday riders. |
| `average_saturday_riders` | double | Average Saturday riders. |
| `average_sunday_or_holiday_riders` | double | Average Sunday/holiday riders. |
| `source_snapshot_id` | varchar | Raw snapshot id. |

## Caveats

- Counts unlinked trips. Metro and Light Rail counting methods changed in Nov 2023. Cross-check mode totals against transit.ntd_monthly.
- 2026-10-14: About 40 routes retired in the 2017 BaltimoreLink redesign appear in ridership history but not in transit.mta_route; the route-list check is therefore a warning, not an error.

## License and citation

```yaml
terms: public dashboard
redistribution: attribution
citation: MDOT MTA Customer Experience Dashboard, retrieved {retrieved_at}
```
