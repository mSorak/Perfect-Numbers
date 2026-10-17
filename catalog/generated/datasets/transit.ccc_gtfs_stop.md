# `transit.ccc_gtfs_stop` — Charm City Circulator GTFS: stops

Bus stops with coordinates. Circulator stop IDs are TripShot UUIDs; no stop ridership is published.

- **Grain:** one row per stop
- **Primary key:** stop_id
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_circulator
- **Depends on:** raw:bcdot_circulator/gtfs
- **Card:** `catalog/datasets/transit/ccc_gtfs_stop.yml`
- **Current build:** 20261017T192527Z · 135 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'bcdot_circulator/gtfs': '20261017T1923Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `stop_id` | varchar | GTFS stop ID. |
| `stop_code` | varchar | Public stop code. |
| `stop_name` | varchar | Stop name. |
| `stop_lat` | double | Latitude. |
| `stop_lon` | double | Longitude. |
| `direction` | varchar | Travel direction at stop (MTA extension; NULL in the Circulator feed). |
| `position` | varchar | Stop position (NS near side, FS far side, MB mid-block; MTA extension; NULL in the Circulator feed). |
| `geometry` | geometry | Point, OGC:CRS84. |
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
