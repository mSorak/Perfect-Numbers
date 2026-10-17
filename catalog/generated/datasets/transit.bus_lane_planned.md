# `transit.bus_lane_planned` — Proposed dedicated bus lanes, East-West Priority Corridor (2024 design update)

Proposed dedicated bus lanes for MTA's East-West Priority Corridor (CityLink Blue/Orange), from the consultant's "Dedicated Bus Lane update oct 10 2024" layer: the Western corridor on Edmondson Ave (Cooks Ln to Warwick Ave) and one Central-corridor piece (President St to Central Ave). Each row is one direction of one extent, typed as 24/7 red-painted or peak-period lanes. Proposed, not built.

- **Grain:** one row per proposed lane extent × direction
- **Primary key:** lane_id
- **Layer / access mode:** staging / mirror
- **Source:** bcdot_bus_lanes
- **Depends on:** raw:bcdot_bus_lanes/ewpc_proposed_2024
- **Card:** `catalog/datasets/transit/bus_lane_planned.yml`
- **Current build:** 20261017T192707Z · 11 rows · git f6eab64
- **Inputs:** {'datasets': {}, 'raw': {'bcdot_bus_lanes/ewpc_proposed_2024': '20261017T1923Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `lane_id` | bigint | Source FID. |
| `corridor` | varchar | Western Corridor or Central Corridor. |
| `extent` | varchar | From–to description, e.g. 'Uplands Pkwy to Wildwood Pkwy'. |
| `lane_type` | varchar | Lane type as published (24/7 Red Painted DBL, Peak Hour DBL, …). |
| `lane_type_group` | varchar | Grouped lane type as published (Type2). |
| `travel_direction` | varchar | north or south as published (the corridor's nominal direction). |
| `hours` | varchar | 24/7 or peak period, derived from lane_type_group. |
| `status` | varchar | Always 'proposed'. |
| `length_m` | double | Line length in metres (EPSG:26985). |
| `source_snapshot_id` | varchar | Raw snapshot id. |
| `geometry` | geometry | LineString, OGC:CRS84. |

## Caveats

- 2026-10-17: A design-stage layer, not a commitment. Check MTA's project page for the current design before citing extents.

## License and citation

```yaml
terms: Public ArcGIS Online item
redistribution: attribution
citation: MDOT MTA East-West Priority Corridor, proposed dedicated bus lanes (Oct
  2024 update), via Mead & Hunt ArcGIS Online (item 5de5bd9cd46648aa86da0644f8e8b7c7),
  retrieved {retrieved_at}
```
