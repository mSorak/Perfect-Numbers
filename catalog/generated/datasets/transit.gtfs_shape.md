# `transit.gtfs_shape` — MTA local bus GTFS: shapes

Route paths as lines assembled from shapes.txt points in sequence.

- **Grain:** one row per shape
- **Primary key:** shape_id
- **Layer / access mode:** staging / mirror
- **Source:** mta_gtfs
- **Depends on:** raw:mta_gtfs/local_bus
- **Card:** `catalog/datasets/transit/gtfs_shape.yml`
- **Current build:** 20261014T020040Z · 588 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'mta_gtfs/local_bus': '20261014T0136Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `shape_id` | varchar | GTFS shape ID. |
| `geometry` | geometry | LineString, OGC:CRS84. |
| `n_points` | bigint | Number of shape points. |
| `feed_snapshot_id` | varchar | Raw snapshot of the GTFS feed this row came from. |

## License and citation

```yaml
terms: Public GTFS feed
redistribution: attribution
citation: MDOT MTA local bus GTFS, feed snapshot {feed_snapshot_id}
```
