# `traffic.bike_facility` — Baltimore City bike facilities (BCDOT)

Bike facilities mapped by Baltimore City DOT, with type, status and installation year.

- **Grain:** one row per mapped facility segment
- **Primary key:** facility_id
- **Layer / access mode:** staging / mirror
- **Source:** baltimore_streets
- **Depends on:** raw:baltimore_streets/bike_facilities
- **Card:** `catalog/datasets/traffic/bike_facility.yml`
- **Current build:** 20261014T020043Z · 628 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'baltimore_streets/bike_facilities': '20261014T0138Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `facility_id` | bigint | Source OBJECTID. |
| `gis_id` | varchar | City GIS ID. |
| `street_name` | varchar | Street name. |
| `from_street` | varchar | From cross street. |
| `to_street` | varchar | To cross street. |
| `facility_type` | varchar | Primary facility type as published. |
| `status` | varchar | Status of the primary facility (existing, planned, …). |
| `facility_type_2` | varchar | Secondary facility type. |
| `status_2` | varchar | Status of the secondary facility. |
| `oneway` | varchar | One-way flag as published. |
| `side` | varchar | Side of street. |
| `install_year` | varchar | Year installed, as published. |
| `owner` | varchar | Owner as published. |
| `length_m` | double | Length in metres (EPSG:26985). |
| `geometry` | geometry | LineString, OGC:CRS84. |

## License and citation

```yaml
terms: Baltimore City open data
redistribution: attribution
citation: Baltimore City DOT, Bike Facilities, retrieved {retrieved_at}
```
