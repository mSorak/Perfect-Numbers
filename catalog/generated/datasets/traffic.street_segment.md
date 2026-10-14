# `traffic.street_segment` — Baltimore City street centerline segments

Every street centerline segment in Baltimore City's enterprise GIS (Street_Centerline_Native), including alleys, ramps and expressways. The basis for joining bus service, jurisdiction and bike facilities to street segments. Subtype codes are kept as published; see caveats for their provisional meanings.

- **Grain:** one row per centerline segment
- **Primary key:** segment_id
- **Layer / access mode:** staging / mirror
- **Source:** baltimore_streets
- **Depends on:** raw:baltimore_streets/street_centerline
- **Card:** `catalog/datasets/traffic/street_segment.yml`
- **Current build:** 20261014T020027Z · 48,522 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'baltimore_streets/street_centerline': '20261014T0137Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | bigint | Source OBJECTID (unique within a snapshot). |
| `cline_id` | varchar | City centerline ID (not fully unique). |
| `county_geoid` | varchar | 24510 (Baltimore city). |
| `street_name` | varchar | Full street name assembled from prefix, name, type and suffix. |
| `from_street` | varchar | Cross street at the segment's start, as published. |
| `to_street` | varchar | Cross street at the segment's end, as published. |
| `subtype_code` | varchar | City segment subtype code (see caveats). |
| `feature_status` | varchar | Status code; A = active (99.6%). |
| `sha_functional_class` | varchar | SHA functional class where assigned: INT interstate, FWY freeway/expressway, PART principal arterial, MART minor arterial, COLL collector, LOC local. |
| `sha_route_id` | varchar | MDOT SHA route ID where the segment is on the state inventory. |
| `sha_id_prefix` | varchar | SHA route prefix (e.g. MD, US, IS, MU). |
| `sha_route_number` | varchar | SHA route number. |
| `length_m` | double | Segment length in metres (EPSG:26985). |
| `source_edit_date` | date | Last edit date in the city GIS. |
| `geometry` | geometry | LineString, OGC:CRS84. |

## Caveats

- 2026-10-14: subtype_code meanings are inferred, not confirmed against the city's schema data dictionary: STRPRD = ordinary street segment, STRALY = alley, STREX = expressway, STRR = ramp, STRXO = crossover, STRTN = tunnel; STRFIC, STRSPR and STRURD unknown. Confirm before publishing breakdowns by subtype.
- segment_id is the source OBJECTID, which can change between city exports. cline_id is the city's line ID but has 8 duplicates or nulls in the 2026-10 export.
- Travel-direction and speed-limit fields are essentially empty in the source and are not carried.
- from_street and to_street are empty for 99.8% of segments in the source.

## License and citation

```yaml
terms: Baltimore City open data
redistribution: attribution
citation: Baltimore City Enterprise GIS, Street Centerline (Native), retrieved {retrieved_at}
```
