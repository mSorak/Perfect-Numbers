# `transit.ccc_gtfs_trip` — Charm City Circulator GTFS: trips

Scheduled trips with route, service calendar, direction and shape.

- **Grain:** one row per scheduled trip
- **Primary key:** trip_id
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_circulator
- **Depends on:** raw:bcdot_circulator/gtfs, transit.ccc_gtfs_route, transit.ccc_gtfs_shape
- **Card:** `catalog/datasets/transit/ccc_gtfs_trip.yml`
- **Current build:** 20261017T192526Z · 2,021 rows · git f6eab64
- **Inputs:** {'datasets': {'transit.ccc_gtfs_route': '20261017T192525Z', 'transit.ccc_gtfs_shape': '20261017T192526Z'}, 'raw': {'bcdot_circulator/gtfs': '20261017T1923Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `trip_id` | varchar | GTFS trip ID. |
| `route_id` | varchar | GTFS route ID. |
| `service_id` | varchar | Service calendar ID (see transit.ccc_gtfs_service_date). |
| `direction_id` | integer | 0/1 direction. |
| `shape_id` | varchar | Shape followed (transit.ccc_gtfs_shape). |
| `headsign` | varchar | Destination sign. |
| `block_id` | varchar | Vehicle block. |
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
