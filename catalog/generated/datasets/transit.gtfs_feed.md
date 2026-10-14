# `transit.gtfs_feed` — MTA local bus GTFS: feed metadata

Feed version and validity dates of the MTA local bus GTFS snapshot in use.

- **Grain:** one row per feed snapshot
- **Primary key:** feed_version
- **Layer / access mode:** staging / mirror
- **Source:** mta_gtfs
- **Depends on:** raw:mta_gtfs/local_bus
- **Card:** `catalog/datasets/transit/gtfs_feed.yml`
- **Current build:** 20261014T0147Z · 1 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'mta_gtfs/local_bus': '20261014T0136Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `feed_version` | varchar | Publisher feed version. |
| `feed_start_date` | date | First service date covered. |
| `feed_end_date` | date | Last service date covered. |
| `publisher` | varchar | Feed publisher. |
| `feed_snapshot_id` | varchar | Raw snapshot of the GTFS feed this row came from. |

## License and citation

```yaml
terms: Public GTFS feed
redistribution: attribution
citation: MDOT MTA local bus GTFS, feed snapshot {feed_snapshot_id}
```
