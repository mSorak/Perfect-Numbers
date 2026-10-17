# `transit.ccc_gtfs_route` — Charm City Circulator GTFS: routes

Routes in the Charm City Circulator GTFS feed.

- **Grain:** one row per route
- **Primary key:** route_id
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_circulator
- **Depends on:** raw:bcdot_circulator/gtfs
- **Card:** `catalog/datasets/transit/ccc_gtfs_route.yml`
- **Current build:** 20261017T192525Z · 5 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'bcdot_circulator/gtfs': '20261017T1923Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `route_id` | varchar | GTFS route ID (TripShot numeric string, e.g. 4965). |
| `route_short_name` | varchar | Route number as published by TripShot (1 Banner, 2 Cherry, 3 Green, 4 Orange, 5 Purple). |
| `route_long_name` | varchar | Route description. |
| `route_type` | integer | GTFS route type (3 = bus). |
| `route_color` | varchar | Hex colour. |
| `network_id` | varchar | Network grouping (MTA extension; NULL in the Circulator feed). |
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
