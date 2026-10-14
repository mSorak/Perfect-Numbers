# `geo.county` — Maryland counties (TIGER/Line 2024)

Analytical-grade (full-resolution) boundaries from the Census Bureau's TIGER/Line 2024 files. Polygons include water; use aland_m2 for land area and density, never polygon area. Coordinates are NAD83, stored as OGC:CRS84 (difference under 2 m).

- **Grain:** one row per county or county-equivalent (24)
- **Primary key:** geoid
- **Layer / access mode:** staging / mirror
- **Source:** census_tiger
- **Depends on:** raw:census_tiger/county_us_2024
- **Card:** `catalog/datasets/geo/county.yml`
- **Current build:** 20261014T0143Z · 24 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'census_tiger/county_us_2024': '20261014T0138Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `geoid` | varchar | Census GEOID (zero-padded text). |
| `geoid_vintage` | integer | Boundary vintage year (2024). |
| `statefp` | varchar | State FIPS (24 = Maryland). |
| `countyfp` | varchar | 3-digit county FIPS. |
| `name` | varchar | County name, e.g. "Baltimore" (city and county share the short name; use name_full or geoid). |
| `name_full` | varchar | Legal/statistical area name, e.g. "Baltimore city". |
| `aland_m2` | bigint | Land area, square metres (Census). |
| `awater_m2` | bigint | Water area, square metres (Census). |
| `geometry` | geometry | Polygon, OGC:CRS84. |

## License and citation

```yaml
terms: public domain
redistribution: allowed
citation: U.S. Census Bureau, TIGER/Line Shapefiles 2024
```
