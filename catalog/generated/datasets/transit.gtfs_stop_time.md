# `transit.gtfs_stop_time` — MTA local bus GTFS: stop times

Scheduled arrival and departure at each stop. Times are seconds after midnight of the service day (can exceed 86,400).

- **Grain:** one row per trip × stop visit
- **Primary key:** trip_id, stop_sequence
- **Layer / access mode:** staging / mirror
- **Source:** mta_gtfs
- **Depends on:** raw:mta_gtfs/local_bus, transit.gtfs_trip
- **Card:** `catalog/datasets/transit/gtfs_stop_time.yml`
- **Current build:** 20261014T020040Z · 1,383,459 rows · git d8c1e6e
- **Inputs:** {'datasets': {'transit.gtfs_trip': '20261014T020040Z'}, 'raw': {'mta_gtfs/local_bus': '20261014T0136Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `trip_id` | varchar | GTFS trip ID. |
| `stop_id` | varchar | GTFS stop ID. |
| `stop_sequence` | integer | Order of the stop within the trip. |
| `arrival_s` | integer | Scheduled arrival, seconds after service-day midnight. |
| `departure_s` | integer | Scheduled departure, seconds after service-day midnight. |
| `shape_dist_traveled` | double | Distance along shape (feed units, miles). |
| `pickup_type` | integer | 0 regular pickup. |
| `drop_off_type` | integer | 0 regular drop-off. |
| `timepoint` | integer | 1 = exact timepoint. |

## License and citation

```yaml
terms: Public GTFS feed
redistribution: attribution
citation: MDOT MTA local bus GTFS, feed snapshot {feed_snapshot_id}
```
