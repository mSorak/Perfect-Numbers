# `transit.bus_segment_summary` — Baltimore City bus corridors by street segment (weekday summary, for mapping)

One row per Baltimore City street segment with scheduled MTA local-bus service. Combines weekday service intensity (peak buses per hour in the busier direction, daily passes, routes), who controls the street, existing bus lanes (OpenStreetMap) and bike facilities (BCDOT), stop activity, and a route-ridership exposure figure. Built to rank candidate bus-lane corridors.

- **Grain:** one row per street segment with weekday bus service
- **Primary key:** segment_id
- **Layer / access mode:** mart / derived
- **Source:** derived
- **Depends on:** transit.bus_segment_service, traffic.street_segment, traffic.road_jurisdiction, traffic.bike_facility, transit.bus_lane_existing, transit.stop_ridership, transit.mta_ridership_route_month, transit.mta_route, transit.gtfs_route
- **Card:** `catalog/datasets/transit/bus_segment_summary.yml`
- **Current build:** 20261014T020318Z · 8,010 rows · git d8c1e6e
- **Inputs:** {'datasets': {'transit.bus_segment_service': '20261014T020219Z', 'traffic.street_segment': '20261014T020027Z', 'traffic.road_jurisdiction': '20261014T020041Z', 'traffic.bike_facility': '20261014T020043Z', 'transit.bus_lane_existing': '20261014T020043Z', 'transit.stop_ridership': '20261014T020043Z', 'transit.mta_ridership_route_month': '20261014T020043Z', 'transit.mta_route': '20261014T020043Z', 'transit.gtfs_route': '20261014T020040Z'}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | bigint | traffic.street_segment.segment_id. |
| `street_name` | varchar | Street name. |
| `sha_functional_class` | varchar | SHA functional class where assigned. |
| `sha_route_id` | varchar | SHA route ID where on the state inventory. |
| `length_m` | double | Segment length in metres. |
| `controller` | varchar | Who maintains the street: Baltimore City, MDTA (state toll), Federal, or Other (from MDOT SHA maintenance responsibility; streets not on that layer are city streets). |
| `on_sha_inventory` | boolean | Segment matched a section of MDOT SHA's roadway inventory (which covers nearly every public road in the city). |
| `weekday_bus_passes` | hugeint | Scheduled weekday bus passes, all bands and directions. |
| `am_peak_buses_per_hour` | double | Weekday 6–9am buses per hour, busier direction. |
| `pm_peak_buses_per_hour` | double | Weekday 3–7pm buses per hour, busier direction. |
| `midday_buses_per_hour` | double | Weekday 9am–3pm buses per hour, busier direction. |
| `n_weekday_routes` | bigint | Distinct weekday routes using the segment. |
| `weekday_routes` | varchar | Weekday route short names, comma-separated. |
| `n_stops` | bigint | Bus stops snapped to this segment (within 30 m). |
| `stop_boardings` | double | Average weekday boardings at those stops (seasonal; all routes). |
| `stop_alightings` | double | Average weekday alightings at those stops. |
| `route_weekday_riders_exposure` | double | Sum of average weekday riders of routes using the segment (see caveats). |
| `has_bus_lane` | boolean | A bus lane runs along the segment per BCDOT (Shared Bus-Bike Lane) or OpenStreetMap. |
| `bus_lane_source` | varchar | Which source flags the bus lane: BCDOT, OSM or BCDOT+OSM. |
| `has_bus_lane_osm` | boolean | An OSM-tagged bus lane runs along the segment. |
| `bus_lane_side_osm` | varchar | Side of the tagged bus lane (right/left/both/lane tags). |
| `bike_facility_type` | varchar | BCDOT bike facility type along the segment, if any. |
| `bike_facility_status` | varchar | Status of that bike facility. |
| `geometry` | geometry | LineString, OGC:CRS84. |

## Parameters

```yaml
stop_snap_m: 30
ridership_months: 12
```

## Caveats

- 2026-10-14: controller comes from MDOT SHA's maintenance-responsibility layer. In Baltimore City that layer shows city maintenance for every road except MDTA toll facilities (I-95, I-395, I-895 and ramps) and federal/NPS roads; MDOT SHA maintains none (2026-10 snapshot). Some MTA routes do run on the MDTA interstates.
- stop_boardings is a seasonal average (Summer 2024 weekday at the 2026-10 pull) and counts all routes at the stop. It measures activity AT the segment, not riders passing through it.
- route_weekday_riders_exposure sums the average weekday riders of every route using the segment (last 12 months). It indicates how many riders' routes use the street, not the passenger load on the segment.
- 2026-10-14: Transit hubs produce very high counts on short access segments: the top segment (25 m of Liberty Heights Ave at the Mondawmin Metro entrance, ~50 buses/hour) reflects ~10 routes converging on the station, not a corridor. For corridor rankings, aggregate by street with length-weighting and exclude short hub-access segments (see queries/examples/bus_corridor_ranking.sql).
- 2026-10-14: has_bus_lane combines BCDOT's 'Shared Bus-Bike Lane' facilities (18.3 km) with OSM bus-lane tags; the two sources only partly overlap (e.g. Lombard St is in BCDOT but not tagged in OSM). Neither is an official complete bus-lane inventory.
