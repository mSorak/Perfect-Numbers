# `ref.county_codes` — Maryland county code crosswalk (FIPS ↔ MDOT/ACRS ↔ names)

One row per Maryland county or county-equivalent. MDOT SHA and ACRS (MDSP crash reports) number counties alphabetically 1–24 with Baltimore City last (24) and Baltimore County 3; these are not FIPS. Join any MDOT/ACRS county code through this table to get `county_geoid`.

- **Grain:** one row per county (24)
- **Primary key:** county_geoid
- **Layer / access mode:** seed / derived
- **Source:** derived
- **Depends on:** seed:ref_county_codes.csv
- **Card:** `catalog/datasets/ref/county_codes.yml`
- **Current build:** 20261014T193421Z · 24 rows · git 839fb53
- **Inputs:** {'datasets': {}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `county_geoid` | varchar | 5-digit county FIPS (24510 = Baltimore city). |
| `county_fips` | varchar | 3-digit county FIPS. |
| `mdot_code` | varchar | MDOT/ACRS alphabetical county code, 1–24 (text; cast to integer to join). |
| `county_name` | varchar | Census county name. |
| `acrs_county_name` | varchar | Name as in ACRS 'Crash County Description'. |
| `mdot_county_desc` | varchar | Name as in MDOT SHA COUNTY_DESC. |

## Caveats

- 2026-10-14: Codes verified against MDOT SHA AADT (COUNTY_ID/COUNTY_DESC, 2026-10 pull) and ACRS (Crash County / Crash County Description, 2024–2025 exports). ACRS codes are zero-padded text ('03'); compare as integers.

## License and citation

```yaml
terms: hand-built from Census FIPS and MDOT/MDSP code lists
redistribution: allowed
```
