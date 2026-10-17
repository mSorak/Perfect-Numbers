# `transit.bus_lane_segment` — Bus lanes on Baltimore City street segments, reconciled across sources

One row per Baltimore City street segment that any bus-lane source flags: OpenStreetMap tags (transit.bus_lane_existing), BCDOT's dedicated-bus-lane inventory (transit.bus_lane_inventory, 2021 copy), BCDOT's bike layer ('Shared Bus-Bike Lane', traffic.bike_facility) and the proposed East-West Priority Corridor lanes (transit.bus_lane_planned). Each source is matched to the segments it runs along with pndata.geo.match_lines_to_segments. bus_lane_status is 'existing' if any existing-lane source flags the segment, else 'proposed' (East-West corridor) or 'recommended' (BCDOT inventory only). The per-source flags are kept so a map or total can choose its own rule.

- **Grain:** one row per street segment flagged by at least one source
- **Primary key:** segment_id
- **Layer / access mode:** mart / derived
- **Source:** derived
- **Depends on:** traffic.street_segment, transit.bus_lane_existing, transit.bus_lane_inventory, traffic.bike_facility, transit.bus_lane_planned
- **Card:** `catalog/datasets/transit/bus_lane_segment.yml`
- **Current build:** 20261017T192805Z · 985 rows · git f6eab64
- **Inputs:** {'datasets': {'traffic.street_segment': '20261014T020027Z', 'transit.bus_lane_existing': '20261017T192710Z', 'transit.bus_lane_inventory': '20261017T192707Z', 'traffic.bike_facility': '20261014T020043Z', 'transit.bus_lane_planned': '20261017T192707Z'}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | bigint | traffic.street_segment.segment_id. |
| `street_name` | varchar | Street name (city centerline). |
| `length_m` | double | Segment length in metres. |
| `bus_lane_status` | varchar | existing, proposed or recommended (rule in description). |
| `n_existing_sources` | integer | How many of the three existing-lane sources (BCDOT inventory current, BCDOT bike layer, OSM) flag the segment. |
| `existing_sources` | varchar | Which existing-lane sources flag it, joined with '+'. |
| `on_osm` | boolean | An OSM bus-lane way runs along the segment. |
| `osm_side` | varchar | OSM bus-lane side(s) (right/left/both/lane tags/busway). |
| `on_bcdot_inventory` | boolean | A current/under-construction piece of the BCDOT inventory runs along the segment. |
| `bcdot_inventory_recommended_only` | boolean | Only 'Recommended' inventory pieces run along the segment. |
| `bcdot_inventory_project` | varchar | Inventory project(s) (North Avenue Streetscape, CHARM CITY CIRCULATOR). |
| `bcdot_inventory_hours` | varchar | Inventory hours (e.g. 24/7) where published. |
| `bcdot_inventory_side` | varchar | Inventory side(s): One side / Both sides. |
| `on_bcdot_bike_layer` | boolean | A BCDOT bike-layer 'Shared Bus-Bike Lane' runs along the segment. |
| `is_proposed_ewpc` | boolean | A proposed East-West Priority Corridor lane runs along the segment. |
| `proposed_hours` | varchar | Proposed lane hours (24/7, peak period). |
| `proposed_corridor` | varchar | East-West corridor section (Western, Central). |
| `geometry` | geometry | Segment centerline, LineString, OGC:CRS84. |

## Parameters

```yaml
buffer_m: 15
min_share: 0.5
max_angle: 30
```

## Caveats

- 2026-10-17: No source is complete or current: the BCDOT inventory dates from 2021, the bike layer only carries shared bus-bike lanes, and OSM depends on volunteers. 'existing' is the union of the three; n_existing_sources shows agreement.
- 2026-10-17: Matching is to street centerlines, so a lane on one side flags the whole segment. Lane-km by side needs the source layers (side columns).
