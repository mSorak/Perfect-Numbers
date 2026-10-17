# Baltimore buses: frequency by street, and where the bus lanes are

Piece for *Perfect Numbers*. Branch `claude/baltimore-buses-*`, one session (see `docs/projects.md`).
Hub datasets used are listed in `project.yml`; scripts in `scripts/` read the hub by dataset ID and write only to `outputs/`.

## Questions

1. **Which Baltimore streets carry the most buses?** Weekday buses per hour by street segment: at the peak, midday and across the day. How much does the Charm City Circulator add downtown?
2. **Where are the bus lanes, and do they sit on the streets with the most buses and riders?** Which high-frequency, high-ridership streets have no bus lane, and who controls those streets (almost always the City)?
3. **How many riders use each street?** No agency publishes this. We estimate it transparently and label every figure as an estimate with a method version.

## Outputs (drafts in `outputs/`)

Every map states the GTFS feeds and service date and, for riders, the ridership window.

| # | Map (by street segment) | Measure | Status |
|---|---|---|---|
| M1 | Weekday **peak hour** buses per hour, MTA only | busiest single clock hour, busier direction | draft |
| M2 | Weekday peak hour, **MTA + Circulator** | same | draft |
| M3 | Weekday **midday** (9 am–3 pm) average, MTA only / MTA + Circulator | busier direction | draft |
| M4 | Weekday **all-day** (daytime 6 am–7 pm average), MTA only / MTA + Circulator | busier direction | draft |
| M5 | **Bus riders** by segment (estimate `riders_v1`), bus lanes overlaid | weekday riders passing | draft |
| M6 | Bus lanes by source (BCDOT inventory, BCDOT bike layer, OSM), planned East–West lanes | reconciliation | draft |

Later candidates: Circulator-only map; bus-lane coverage chart (share of high-frequency street-km with a lane, by controller); before/after on North Ave.

## Data inventory

### Already in the hub (Phase 1)
| Dataset | What | Window |
|---|---|---|
| `transit.bus_segment_service` | MTA local-bus passes per segment × day type × band × direction | GTFS snapshot 2026-10-14; weekday 2026-10-14 |
| `transit.bus_segment_summary` | weekday summary per segment, jurisdiction, lanes (OSM + BCDOT bike layer), stop activity | as above |
| `transit.stop_ridership` | avg weekday boardings/alightings per MTA stop, all routes | Summer 2024 season (iMAP, pulled 2026-10) |
| `transit.mta_ridership_route_month` | avg weekday riders per route, monthly | 2011-07 → 2026-09 |
| `transit.bus_lane_existing` | OSM ways tagged with bus lanes | Overpass 2026-10-14 |
| `traffic.street_segment`, `traffic.road_jurisdiction`, `traffic.bike_facility` | city centerlines, who maintains each road, BCDOT bike layer (includes "Shared Bus-Bike Lane") | 2026-10 |
| `transit.ntd_monthly` | **Circulator system ridership** (NTD 30201 "City of Baltimore", mode MB, purchased transportation) | 2015-07 → 2026-08 |

### Pulled for this piece (2026-10-17)
| Source → dataset | What | Notes |
|---|---|---|
| `bcdot_circulator` → `transit.ccc_gtfs_*` | **Charm City Circulator GTFS** from TripShot (`charmcity.tripshot.com/v1/gtfs.zip`), 5 routes: Purple, Orange, Green, Banner, Cherry | The city's old download links (`cccgtfs824zip`, Jan 2024) are dead and Mobility Database marks them deprecated. The Circulator moved to TripShot in July 2026. The feed's calendars start 2026-09-06. |
| `bcdot_bus_lanes` → `transit.bus_lane_inventory` | **BCDOT dedicated-bus-lane inventory** ("Bus Lane" layer, BCDOT facility schema) | No BCDOT or MTA open layer exists. This is the copy hosted by Mead & Hunt (BCDOT-tagged web map "RHRs, Separated Bike Lanes and Bus Lanes", last edited 2021-11). Has status (current vs. recommended), project and hours. |
| `bcdot_bus_lanes` → `transit.bus_lane_planned` | **East–West Priority Corridor** proposed dedicated bus lanes (Oct 2024 design update) | Western corridor (Edmondson Ave, Cooks Ln → Warwick) and a Central-corridor segment; 24/7 red vs. peak-period lanes. Proposed, not built. |
| `bcdot_bus_lanes` (document) | MTA "Dedicated Bus Lanes" downtown map (PDF, Oct 2017) | Reference for downtown lane hours (curbside / parking-adjacent / peak). Not parsed. |
| `transit.bus_lane_segment` (mart) | Reconciled bus-lane flags per street segment across OSM, BCDOT inventory, BCDOT bike layer and planned lanes | |

### Not available (documented)
- **Circulator ridership by route or stop:** not published. Open Baltimore's old "Charm City Circulator Ridership" dataset (Socrata `wwvu-583r`, ca. 2013) is gone. Only the **system** total is available, monthly from NTD (≈120–140k trips a month in 2025–26).
- **Official current bus-lane GIS:** none public from BCDOT or MTA (checked the BCDOT ArcGIS org's 143 services, Open Baltimore, iMAP, MTA's site). MTA says BaltimoreLink built "a 5.5 mile network". Lanes built after 2021 (e.g. any York Rd pilot) may be missing from the 2021 inventory and must be checked against OSM and street imagery.
- **Other shuttles on the same streets (noted, not pulled):** Harbor Connector (ferry, GTFS on Mobility Database `mdb-618`), Johns Hopkins JHMI/Homewood shuttles, University of Maryland Baltimore shuttle, UMBC/Towson shuttles (Towson Loop GTFS `mdb-1784`, outside the city). MTA commuter bus (CityLink/LocalLink only in the hub today) also uses downtown streets and is a candidate addition.

## Methods

### Buses per hour (scheduled)
- **Source:** GTFS schedules. MTA local bus (snapshot used by `transit.bus_segment_service`) and Circulator (TripShot). Representative weekday **Wednesday 2026-10-14**.
- **Matching:** each route shape is matched to the street segments it runs *along* with `pndata.geo.match_lines_to_segments` (≥60% of the segment within 10 m, bearing within 30°). Pass time at a segment is interpolated between the trip's first and last stop times.
- **Busier direction:** passes counted "with" and "against" the segment's digitized direction; maps show the busier direction (what a one-direction bus lane serves). For MTA + Circulator, directions are summed first, then the max is taken.
- **Peak hour:** the busiest single clock hour of the weekday (`transit.bus_segment_hour`). **Midday:** 9 am–3 pm average. **All-day:** 6 am–7 pm average (13 h; covers the Circulator's weekday span, 7 am–8 pm). Daily passes are also kept.
- **Caveats:** scheduled, not observed, service (MTA on-time performance and missed trips are not reflected). Divided roads credit both carriageways with both directions. Short hub-access segments (Mondawmin, State Center) show station convergence, not corridors: map styling de-emphasises segments under 50 m. The Saturday sample date (2026-10-17) was the Baltimore Running Festival, when the Circulator was suspended 9–4; GTFS does not show that, so Saturday maps need a different date.

### Riders by segment (estimates, labelled)
Nobody publishes passenger load by street. Candidate methods, from simplest to best:

- **`stops_v1` — stop activity on the segment.** Boardings + alightings at stops snapped to the segment (Summer 2024, all routes). Measures activity *at* the street, not riders passing through. Already in `bus_segment_summary`.
- **`exposure_v1` — route riders, trip-weighted.** Σ over routes of the route's average weekday riders (CX, last 12 months) × the share of that route's weekday trips that use the segment. An **upper bound** on load: it assumes every rider rides the whole route.
- **`riders_v1` — load profile from stop ons/offs (recommended).** For each MTA route pattern (shape × direction), allocate each stop's boardings and alightings to the patterns serving it in proportion to scheduled trips. Walk the stop sequence: load after stop *k* = Σ(ons − offs) up to *k*, rebalanced so each pattern starts and ends at zero. Scale each route's daily total to its CX average weekday riders (last 12 months), then credit each inter-stop link's load to the segments between those stops. Sum across patterns. Output: estimated weekday riders passing each segment, both directions and busier direction.
  - Caveats: stop counts are seasonal (Summer 2024) and not route-specific; trip-proportional allocation at shared stops is an assumption; scaling mixes Summer 2024 stop shares with 2025–26 route totals.
  - **Circulator:** no stop or route counts. `riders_v1` excludes it. An optional `riders_v1_ccc` would allocate NTD system trips to routes by scheduled trips and spread them evenly along each route. Labelled as a rough estimate.

## Decisions (dated)
- 2026-10-17: Circulator GTFS from TripShot (the only live feed). The feed carries no `feed_info` dates or version, so the snapshot ID and calendar range identify it.
- 2026-10-17: The official bus-lane source is the BCDOT inventory as hosted by Mead & Hunt (2021), reconciled with OSM. No single source is complete. A segment is flagged **existing** when the BCDOT inventory (current) or BCDOT bike layer (Shared Bus-Bike Lane) or OSM says so; the source is kept per flag.
- 2026-10-17: MTA-only and MTA + Circulator versions of every frequency map. The Circulator is free and city-run, so it is part of what a rider downtown sees.

## Open decisions for Matt
1. Peak = busiest single clock hour (current draft) or the 3-hour band average (7–9 am / 4–6 pm)?
2. Does the riders map use `riders_v1` (load profile), or the simpler upper-bound `exposure_v1`? And should the Circulator be added with the rough `riders_v1_ccc`?
3. The bus-lane source: is the 2021 BCDOT inventory acceptable with a caveat, or should we ask BCDOT for a current list (MPIA or press office)?
4. Should MTA commuter buses be added to the hub (they use downtown streets in the peak)?

## Status
- 2026-10-17: Plan written. Circulator GTFS and bus-lane sources added to the hub; segment marts extended; first draft maps in `outputs/` (see the end of this file once built).
