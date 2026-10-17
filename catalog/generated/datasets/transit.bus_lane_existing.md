# `transit.bus_lane_existing` — Existing bus lanes in Baltimore (OpenStreetMap)

Street ways in Baltimore tagged with a bus lane or busway in OpenStreetMap, from a bounded Overpass query. No official public bus-lane layer from BCDOT or MTA was found (2026-10). Completeness depends on volunteer mapping, so verify against BCDOT/MTA materials before publishing totals.

- **Grain:** one row per OSM way with bus-lane tags
- **Primary key:** osm_way_id
- **Layer / access mode:** staging / mirror
- **Source:** osm_overpass
- **Depends on:** raw:osm_overpass/baltimore_bus_lanes
- **Card:** `catalog/datasets/transit/bus_lane_existing.yml`
- **Current build:** 20261017T192710Z · 154 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'osm_overpass/baltimore_bus_lanes': '20261017T1924Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `osm_way_id` | bigint | OpenStreetMap way ID. |
| `street_name` | varchar | OSM name tag. |
| `highway` | varchar | OSM highway class. |
| `bus_lane_side` | varchar | right, left, both, 'lane tags' (lanes:bus style tagging) or busway. |
| `busway_tag` | varchar | Value of the busway:* tag (usually 'lane'). |
| `lanes_bus` | varchar | Value of lanes:bus / bus:lanes if present. |
| `colour` | varchar | Lane colour if tagged (e.g. red). |
| `start_date` | varchar | Installation date if tagged. |
| `oneway` | varchar | OSM oneway tag. |
| `source_snapshot_id` | varchar | Raw snapshot id. |
| `geometry` | geometry | LineString, OGC:CRS84. |

## Caveats

- 2026-10-14: 154 ways at first pull, concentrated on North Ave, Baltimore St, Pratt St, Fayette St and Gay St. Not verified against an official list.

## License and citation

```yaml
terms: ODbL 1.0
redistribution: attribution + share-alike for derived databases
citation: "\xA9 OpenStreetMap contributors"
```
