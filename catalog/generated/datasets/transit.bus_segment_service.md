# `transit.bus_segment_service` — Scheduled bus service on Baltimore City street segments, by operator and time band

Scheduled bus passes on each Baltimore City street segment, by operator (MTA local bus; Charm City Circulator), for a representative weekday, Saturday and Sunday, split into time bands and by direction. Derived from the MTA local-bus and Circulator GTFS feeds: each route shape is matched to the segments it runs along (at least 60% of the segment within 10 m of the shape, and bearing within 30°, so cross streets at intersections are excluded). Each trip's time at a segment is interpolated between its first departure and last arrival. "with"/"against" is relative to the segment's digitized direction, a proxy for the two travel directions.
Rows are per operator; to combine operators, sum n_passes_with and n_passes_against before taking the busier direction.

- **Grain:** one row per segment × operator × day type × time band (bands with no service are absent)
- **Primary key:** segment_id, operator, day_type, time_band
- **Layer / access mode:** mart / derived
- **Source:** derived
- **Depends on:** traffic.street_segment, transit.gtfs_shape, transit.gtfs_trip, transit.gtfs_stop_time, transit.gtfs_route, transit.gtfs_service_date, transit.ccc_gtfs_shape, transit.ccc_gtfs_trip, transit.ccc_gtfs_stop_time, transit.ccc_gtfs_route, transit.ccc_gtfs_service_date
- **Card:** `catalog/datasets/transit/bus_segment_service.yml`
- **Current build:** 20261017T192952Z · 136,113 rows · git f6eab64
- **Inputs:** {'datasets': {'traffic.street_segment': '20261014T020027Z', 'transit.gtfs_shape': '20261014T020040Z', 'transit.gtfs_trip': '20261014T020040Z', 'transit.gtfs_stop_time': '20261014T020040Z', 'transit.gtfs_route': '20261014T020040Z', 'transit.gtfs_service_date': '20261014T020041Z', 'transit.ccc_gtfs_shape': '20261017T192526Z', 'transit.ccc_gtfs_trip': '20261017T192526Z', 'transit.ccc_gtfs_stop_time': '20261017T192526Z', 'transit.ccc_gtfs_route': '20261017T192525Z', 'transit.ccc_gtfs_service_date': '20261017T192527Z'}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | bigint | traffic.street_segment.segment_id. |
| `operator` | varchar | MTA (local bus feed) or Circulator (Charm City Circulator feed). |
| `day_type` | varchar | weekday, saturday or sunday (representative dates in parameters). |
| `time_band` | varchar | early, am_peak, midday, pm_peak, evening, night. |
| `band_hours` | integer | Length of the time band in hours. |
| `n_bus_passes` | bigint | Scheduled bus passes in the band, both directions. |
| `n_passes_with` | bigint | Passes travelling in the segment's digitized direction. |
| `n_passes_against` | bigint | Passes travelling against the segment's digitized direction. |
| `buses_per_hour_max_direction` | double | Buses per hour in the busier direction (the relevant figure for a directional bus lane). |
| `buses_per_hour_both_directions` | double | Buses per hour, both directions combined. |
| `n_routes` | bigint | Distinct routes (by short name) passing in the band. |
| `routes` | varchar[] | Route short names passing in the band. |

## Parameters

```yaml
service_dates:
  weekday: '2026-10-14'
  saturday: '2026-10-17'
  sunday: '2026-10-18'
buffer_m: 10
min_share: 0.6
max_angle: 30
time_bands: early 4–6, am_peak 6–9, midday 9–15, pm_peak 15–19, evening 19–24, night
  24–28 (hours after service-day midnight)
```

## Caveats

- Pass times are interpolated linearly along each trip; on long routes the band assignment for a segment can be off by up to a band boundary.
- 2026-10-14: Matcher QA (360 weekday shapes with >500 m in the city): matched segment length ÷ in-city shape length has median 1.04 and 5th–95th percentile 0.96–1.25 at a 10 m buffer. The excess is mostly divided roads, where both carriageways are credited with buses from both directions; per-segment intensity is unaffected but corridor kilometres are slightly overstated. 14 shapes match under 90% of their in-city length (off-street terminals and loops).
- MTA local bus and the Charm City Circulator only: MTA commuter bus, Light Rail, Metro, the Harbor Connector and university shuttles are not included.
- 2026-10-17: Saturday 2026-10-17 was the Baltimore Running Festival; the Circulator suspended Orange, Purple and Banner 9 am–4 pm and MTA detoured routes. Neither GTFS shows it, so Saturday rows describe the regular schedule, not that day.
- 2026-10-17: The Circulator feed schedules 16 extra Orange Route trips 8–11 pm every day (no direction_id), although BCDOT publishes Mon–Thu service ending at 8 pm. They affect only the evening band.
