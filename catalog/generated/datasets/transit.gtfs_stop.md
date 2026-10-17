# `transit.gtfs_stop` — MTA local bus GTFS: stops

Bus stops with coordinates. stop_id matches Stop_ID in transit.stop_ridership.

- **Grain:** one row per stop
- **Primary key:** stop_id
- **Layer / access mode:** staging / mirror
- **Source:** mta_gtfs
- **Depends on:** raw:mta_gtfs/local_bus
- **Card:** `catalog/datasets/transit/gtfs_stop.yml`
- **Current build:** 20261017T193303Z · 4,056 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'mta_gtfs/local_bus': '20261014T0136Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `stop_id` | varchar | GTFS stop ID. |
| `stop_code` | varchar | Public stop code. |
| `stop_name` | varchar | Stop name. |
| `stop_lat` | double | Latitude. |
| `stop_lon` | double | Longitude. |
| `direction` | varchar | Travel direction at stop (MTA extension). |
| `position` | varchar | Stop position (NS near side, FS far side, MB mid-block; MTA extension). |
| `geometry` | geometry | Point, OGC:CRS84. |
| `feed_snapshot_id` | varchar | Raw snapshot of the GTFS feed this row came from. |

## License and citation

```yaml
terms: Public GTFS feed
redistribution: attribution
citation: MDOT MTA local bus GTFS, feed snapshot {feed_snapshot_id}
```
