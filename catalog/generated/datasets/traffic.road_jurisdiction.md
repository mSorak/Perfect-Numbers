# `traffic.road_jurisdiction` — Road maintenance responsibility (MDOT SHA), Baltimore City + County

Which agency maintains each section of road on MDOT SHA's roadway inventory, for Baltimore City and Baltimore County. Roads absent from this layer are local streets maintained by the city or county.

- **Grain:** one row per inventory road section
- **Primary key:** section_id
- **Layer / access mode:** staging / mirror
- **Source:** mdot_sha_roads
- **Depends on:** raw:mdot_sha_roads/maintenance_responsibility
- **Card:** `catalog/datasets/traffic/road_jurisdiction.yml`
- **Current build:** 20261014T020041Z · 16,579 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'mdot_sha_roads/maintenance_responsibility': '20261014T0137Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `section_id` | varchar | Source GlobalID. |
| `county_geoid` | varchar | 24510 Baltimore city or 24005 Baltimore County. |
| `mdot_county_code` | integer | MDOT alphabetical county code (24 = Baltimore City, 3 = Baltimore County); not FIPS. |
| `road_name` | varchar | Road name as published. |
| `id_prefix` | varchar | Route prefix (IS, US, MD, MU, CO, …). |
| `route_number` | varchar | Route number. |
| `route_id_rh` | varchar | SHA route ID. |
| `from_measure_mi` | double | Start milepoint. |
| `to_measure_mi` | double | End milepoint. |
| `govt_control_code` | varchar | HPMS ownership/control code. |
| `maintenance_responsibility` | varchar | Maintaining agency as published. |
| `maintainer_group` | varchar | Grouped: MDOT SHA, MDTA (state toll), County, City/municipal, Federal, Other. |
| `main_line` | varchar | Main line flag as published. |
| `municipality` | varchar | Municipality name if any. |
| `length_m` | double | Section length in metres (EPSG:26985). |
| `geometry` | geometry | LineString/MultiLineString, OGC:CRS84. |

## Caveats

- 2026-10-14: In the 2026-10 snapshot no Baltimore City section is maintained by MDOT SHA: inventory roads there are city-maintained, MDTA toll roads, or federal/NPS. Verify against MDOT SHA before stating as fact.

## License and citation

```yaml
terms: public
redistribution: attribution
citation: MDOT SHA, Roadway Maintenance Responsibility, retrieved {retrieved_at}
```
