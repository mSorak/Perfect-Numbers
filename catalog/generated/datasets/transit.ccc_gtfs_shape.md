# `transit.ccc_gtfs_shape` — Charm City Circulator GTFS: shapes

Route paths as lines assembled from shapes.txt points in sequence.

- **Grain:** one row per shape
- **Primary key:** shape_id
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_circulator
- **Depends on:** raw:bcdot_circulator/gtfs
- **Card:** `catalog/datasets/transit/ccc_gtfs_shape.yml`
- **Current build:** 20261017T192526Z · 114 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'bcdot_circulator/gtfs': '20261017T1923Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `shape_id` | varchar | GTFS shape ID. |
| `geometry` | geometry | LineString, OGC:CRS84. |
| `n_points` | bigint | Number of shape points. |
| `feed_snapshot_id` | varchar | Raw snapshot of the GTFS feed this row came from. |

## Parameters

```yaml
raw: bcdot_circulator/gtfs
```

## Caveats

- 2026-10-17: TripShot feed: IDs are UUIDs that may change between feed versions; join only within one snapshot. feed_info has no dates or version.

## License and citation

```yaml
terms: Public GTFS feed (published for trip-planning apps)
redistribution: attribution
citation: Baltimore City DOT, Charm City Circulator GTFS (TripShot), feed snapshot
  {feed_snapshot_id}
```
