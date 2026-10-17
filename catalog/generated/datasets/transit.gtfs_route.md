# `transit.gtfs_route` — MTA local bus GTFS: routes

Routes in the MTA local bus GTFS feed. route_id joins to transit.mta_route.route_id_gtfs (CX dashboard ridership).

- **Grain:** one row per route
- **Primary key:** route_id
- **Layer / access mode:** staging / mirror
- **Source:** mta_gtfs
- **Depends on:** raw:mta_gtfs/local_bus
- **Card:** `catalog/datasets/transit/gtfs_route.yml`
- **Current build:** 20261017T193303Z · 66 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'mta_gtfs/local_bus': '20261014T0136Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `route_id` | varchar | GTFS route ID (numeric string, e.g. 11684). |
| `route_short_name` | varchar | Public route name (e.g. 103, CityLink BLUE). |
| `route_long_name` | varchar | Route description. |
| `route_type` | integer | GTFS route type (3 = bus). |
| `route_color` | varchar | Hex colour. |
| `network_id` | varchar | MTA network grouping (e.g. core). |
| `feed_snapshot_id` | varchar | Raw snapshot of the GTFS feed this row came from. |

## License and citation

```yaml
terms: Public GTFS feed
redistribution: attribution
citation: MDOT MTA local bus GTFS, feed snapshot {feed_snapshot_id}
```
