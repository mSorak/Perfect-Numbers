# `transit.bus_segment_service` — Scheduled MTA bus service on Baltimore City street segments, by time band

Scheduled bus passes on each Baltimore City street segment, for a representative weekday, Saturday and Sunday, split into time bands and by direction. Derived from MTA local-bus GTFS: each route shape is matched to the segments it runs along (at least 60% of the segment within 10 m of the shape, and bearing within 30°, so cross streets at intersections are excluded). Each trip's time at a segment is interpolated between its first departure and last arrival. "with"/"against" is relative to the segment's digitized direction, a proxy for the two travel directions.

- **Grain:** one row per segment × day type × time band (bands with no service are absent)
- **Primary key:** segment_id, day_type, time_band
- **Layer / access mode:** mart / derived
- **Source:** derived
- **Depends on:** traffic.street_segment, transit.gtfs_shape, transit.gtfs_trip, transit.gtfs_stop_time, transit.gtfs_route, transit.gtfs_service_date
- **Card:** `catalog/datasets/transit/bus_segment_service.yml`
- **Current build:** 20261014T020219Z · 129,670 rows · git d8c1e6e
- **Inputs:** {'datasets': {'traffic.street_segment': '20261014T020027Z', 'transit.gtfs_shape': '20261014T020040Z', 'transit.gtfs_trip': '20261014T020040Z', 'transit.gtfs_stop_time': '20261014T020040Z', 'transit.gtfs_route': '20261014T020040Z', 'transit.gtfs_service_date': '20261014T020041Z'}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | bigint | traffic.street_segment.segment_id. |
| `day_type` | varchar | weekday, saturday or sunday (representative dates in parameters). |
| `time_band` | varchar | early, am_peak, midday, pm_peak, evening, night. |
| `band_hours` | integer | Length of the time band in hours. |
| `n_bus_passes` | bigint | Scheduled bus passes in the band, both directions. |
| `n_passes_with` | bigint | Passes travelling in the segment's digitized direction. |
| `n_passes_against` | bigint | Passes travelling against the segment's digitized direction. |
| `buses_per_hour_max_direction` | double | Buses per hour in the busier direction (the relevant figure for a directional bus lane). |
| `buses_per_hour_both_directions` | double | Buses per hour, both directions combined. |
| `n_routes` | bigint | Distinct GTFS routes passing in the band. |
| `routes` | varchar[] | Route short names passing in the band. |

## Caveats

- Pass times are interpolated linearly along each trip; on long routes the band assignment for a segment can be off by up to a band boundary.
- Local-bus feed only: commuter bus, Light Rail and Metro are not included.
- 2026-10-14: Matcher QA (360 weekday shapes with >500 m in the city): matched segment length ÷ in-city shape length has median 1.04 and 5th–95th percentile 0.96–1.25 at a 10 m buffer. The excess is mostly divided roads, where both carriageways are credited with buses from both directions; per-segment intensity is unaffected but corridor kilometres are slightly overstated. 14 shapes match under 90% of their in-city length (off-street terminals and loops).
