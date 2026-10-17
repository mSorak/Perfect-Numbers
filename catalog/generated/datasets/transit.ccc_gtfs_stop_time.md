# `transit.ccc_gtfs_stop_time` — Charm City Circulator GTFS: stop times

Scheduled arrival and departure at each stop. Times are seconds after midnight of the service day (can exceed 86,400).

- **Grain:** one row per trip × stop visit
- **Primary key:** trip_id, stop_sequence
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_circulator
- **Depends on:** raw:bcdot_circulator/gtfs, transit.ccc_gtfs_trip
- **Card:** `catalog/datasets/transit/ccc_gtfs_stop_time.yml`
- **Current build:** 20261017T192526Z · 31,620 rows · git f6eab64
- **Inputs:** {'datasets': {'transit.ccc_gtfs_trip': '20261017T192526Z'}, 'raw': {'bcdot_circulator/gtfs': '20261017T1923Z'}}

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
