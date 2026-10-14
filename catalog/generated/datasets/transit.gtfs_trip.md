# `transit.gtfs_trip` — MTA local bus GTFS: trips

Scheduled trips with route, service calendar, direction and shape.

- **Grain:** one row per scheduled trip
- **Primary key:** trip_id
- **Layer / access mode:** staging / mirror
- **Source:** mta_gtfs
- **Depends on:** raw:mta_gtfs/local_bus, transit.gtfs_route, transit.gtfs_shape
- **Card:** `catalog/datasets/transit/gtfs_trip.yml`
- **Current build:** 20261014T020040Z · 27,699 rows · git d8c1e6e
- **Inputs:** {'datasets': {'transit.gtfs_route': '20261014T020040Z', 'transit.gtfs_shape': '20261014T020040Z'}, 'raw': {'mta_gtfs/local_bus': '20261014T0136Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `trip_id` | varchar | GTFS trip ID. |
| `route_id` | varchar | GTFS route ID. |
| `service_id` | varchar | Service calendar ID (see transit.gtfs_service_date). |
| `direction_id` | integer | 0/1 direction. |
| `shape_id` | varchar | Shape followed (transit.gtfs_shape). |
| `headsign` | varchar | Destination sign. |
| `block_id` | varchar | Vehicle block. |
| `feed_snapshot_id` | varchar | Raw snapshot of the GTFS feed this row came from. |

## License and citation

```yaml
terms: Public GTFS feed
redistribution: attribution
citation: MDOT MTA local bus GTFS, feed snapshot {feed_snapshot_id}
```
