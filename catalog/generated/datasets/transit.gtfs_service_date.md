# `transit.gtfs_service_date` — MTA local bus GTFS: active service by date

Which service calendars run on each date, from calendar.txt with calendar_dates.txt exceptions applied (e.g. Labor Day runs Sunday service).

- **Grain:** one row per service date × service_id
- **Primary key:** date, service_id
- **Layer / access mode:** staging / mirror
- **Source:** mta_gtfs
- **Depends on:** raw:mta_gtfs/local_bus
- **Card:** `catalog/datasets/transit/gtfs_service_date.yml`
- **Current build:** 20261014T020041Z · 231 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'mta_gtfs/local_bus': '20261014T0136Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `service_id` | varchar | Service calendar ID. |
| `date` | date | Service date. |

## License and citation

```yaml
terms: Public GTFS feed
redistribution: attribution
citation: MDOT MTA local bus GTFS, feed snapshot {feed_snapshot_id}
```
