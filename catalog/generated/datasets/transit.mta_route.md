# `transit.mta_route` — MTA routes (CX dashboard dimension)

Route list from the MTA Customer Experience dashboard data model, with the GTFS route ID used to join ridership to schedules and shapes.

- **Grain:** one row per CX route
- **Primary key:** route_id
- **Layer / access mode:** staging / mirror
- **Source:** mta_cx_powerbi
- **Depends on:** raw:mta_cx_powerbi/dim_route, raw:mta_cx_powerbi/dim_mode
- **Card:** `catalog/datasets/transit/mta_route.yml`
- **Current build:** 20261014T020043Z · 110 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'mta_cx_powerbi/dim_route': '20261014T0137Z', 'mta_cx_powerbi/dim_mode': '20261014T0138Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `route_id` | varchar | CX dashboard route ID (e.g. 103, BL for CityLink Blue). |
| `route_short_name` | varchar | Public route name. |
| `route_long_name` | varchar | Route description. |
| `mode_id` | bigint | CX mode ID. |
| `mode_name` | varchar | Mode name. |
| `route_type` | varchar | Route type as published. |
| `route_id_gtfs` | varchar | GTFS route_id (joins transit.gtfs_route). |
| `line_abbr_trapeze` | varchar | Scheduling-system line abbreviation. |
| `location` | varchar | Location label as published. |

## Caveats

- Undocumented Power BI endpoint; re-fetches may fail if MTA republishes the report.

## License and citation

```yaml
terms: public dashboard
redistribution: attribution
citation: MDOT MTA Customer Experience Dashboard, retrieved {retrieved_at}
```
