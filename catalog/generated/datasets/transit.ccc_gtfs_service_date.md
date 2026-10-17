# `transit.ccc_gtfs_service_date` — Charm City Circulator GTFS: active service by date

Which service calendars run on each date, from calendar.txt with calendar_dates.txt exceptions applied (the TripShot feed has no exceptions).

- **Grain:** one row per service date × service_id
- **Primary key:** date, service_id
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_circulator
- **Depends on:** raw:bcdot_circulator/gtfs
- **Card:** `catalog/datasets/transit/ccc_gtfs_service_date.yml`
- **Current build:** 20261017T192527Z · 4,416 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'bcdot_circulator/gtfs': '20261017T1923Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `service_id` | varchar | Service calendar ID. |
| `date` | date | Service date. |

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
