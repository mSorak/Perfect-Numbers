# `transit.bus_lane_inventory` — BCDOT dedicated bus-lane inventory (2021 copy)

Baltimore City DOT's dedicated-bus-lane line layer, in BCDOT's facility schema (the same schema as the bike facility layer), as hosted by MTA's consultant Mead & Hunt in a BCDOT-tagged ArcGIS Online map ("Baltimore City RHRs, Separated Bike Lanes, and Bus Lanes"). Each row is a block-level piece of lane with its status (current or under construction vs. recommended), project (North Avenue Streetscape, Charm City Circulator, …), side and hours. The nearest thing to an official bus-lane list that is public; reconcile with OSM via transit.bus_lane_segment.

- **Grain:** one row per mapped lane piece (usually one block, one side)
- **Primary key:** lane_id
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_bus_lanes
- **Depends on:** raw:bcdot_bus_lanes/bus_lane_2021
- **Card:** `catalog/datasets/transit/bus_lane_inventory.yml`
- **Current build:** 20261017T192707Z · 307 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'bcdot_bus_lanes/bus_lane_2021': '20261017T1923Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `lane_id` | bigint | Source OBJECTID. |
| `gis_id` | varchar | BCDOT facility GIS ID. |
| `city_street_id` | varchar | City street ID (ST_ID) as published. |
| `street_name` | varchar | Street name as published (upper case). |
| `block_text` | varchar | Block description, e.g. '300 BLK W LOMBARD ST'. |
| `from_street` | varchar | From cross street (mostly empty). |
| `to_street` | varchar | To cross street (mostly empty). |
| `inventory_status` | varchar | 'Current/Under Construction' or 'Recommended' (DBL_Type). |
| `is_current` | boolean | inventory_status = 'Current/Under Construction'. |
| `facility_type` | varchar | BCDOT facility type (Shared Bus-Bike Lane where filled). |
| `status_code` | varchar | BCDOT STATUS1 code as published (undocumented). |
| `oneway` | varchar | One-way flag as published. |
| `side` | varchar | 'One side' or 'Both sides'. |
| `lane_count` | integer | Number of bus lanes as published. |
| `project` | varchar | Project that built the lane (e.g. North Avenue Streetscape, CHARM CITY CIRCULATOR). |
| `owner` | varchar | Owner as published (BCDOT where filled). |
| `hours_open` | varchar | Hours the lane is bus-only, as published (e.g. 24/7). |
| `length_m` | double | Line length in metres (EPSG:26985). |
| `source_snapshot_id` | varchar | Raw snapshot id. |
| `geometry` | geometry | LineString, OGC:CRS84. |

## Caveats

- 2026-10-17: Last edited 2021-11 upstream. Lanes built or removed since then are not reflected; check against OSM (transit.bus_lane_existing) and imagery before publishing totals. 26 pieces are 'Recommended', not built.
- 2026-10-17: 68 pieces have no street name or facility type (42 current, 26 recommended); they still carry geometry and status. 'One side' vs 'Both sides' is in `side`; when both sides are drawn as one line, lane-km is under-counted by length_m.
- 2026-10-17: status_code is BCDOT's STATUS1 code (2 on every row that has one); its meaning is not documented. Use inventory_status.

## License and citation

```yaml
terms: Public ArcGIS Online item
redistribution: attribution
citation: Baltimore City DOT bus-lane layer, via Mead & Hunt ArcGIS Online (item 91dc583522d04fc5a90079f6e0d0ac46),
  retrieved {retrieved_at}
```
