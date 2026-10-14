# `econ.cpi_u` — Consumer Price Index for All Urban Consumers (CPI-U), BLS

CPI-U all-items index levels (1982-84=100), monthly and annual average, for the U.S. city average (not seasonally adjusted and seasonally adjusted) and Baltimore-Columbia-Towson (NSA). Use the NSA U.S. series CUUR0000SA0 for inflation adjustment (metric `to_real_dollars`); crash-cost method 2026.1 uses June 2019 → June 2025.

- **Grain:** one row per series × year × period
- **Primary key:** series_id, year, period
- **Layer / access mode:** staging / mirror
- **Source:** bls
- **Depends on:** raw:bls/cpi_u
- **Card:** `catalog/datasets/econ/cpi_u.yml`
- **Current build:** 20261014T210200Z · 1,631 rows · git c2a0ea2
- **Inputs:** {'datasets': {}, 'raw': {'bls/cpi_u': '20261014T1930Z'}}
- **Coverage:** 1975-01-01 → 2026-09-01

## Columns

| Column | Type | Description |
|---|---|---|
| `series_id` | varchar | BLS series ID (CUUR0000SA0 U.S. NSA, CUSR0000SA0 U.S. SA, CUURS35ESA0 Baltimore NSA). |
| `area` | varchar | Area the index covers. |
| `is_seasonally_adjusted` | boolean | True for seasonally adjusted series. |
| `year` | integer | Reference year. |
| `period` | varchar | BLS period code: M01–M12 month, M13 annual average, S01/S02 half-year. |
| `period_type` | varchar | month, annual_average or half_year. |
| `month` | date | First day of the month (null for annual and half-year rows). |
| `cpi` | double | Index level, 1982-84=100. Null where BLS published no value. |
| `base` | varchar | Index base period. |
| `footnotes` | varchar | BLS footnotes, if any (e.g. preliminary). |

## Caveats

- 2026-10-14: October 2025 has no published value (data not collected during the federal shutdown); cpi is null for that month. Annual average 2025 is as published by BLS.
- 2026-10-14: Baltimore-Columbia-Towson is published bimonthly in recent years, with gaps in its history (34 annual averages 1975–2025); months without a release are absent. The API returned no half-year (S01/S02) rows.

## License and citation

```yaml
terms: public domain
redistribution: allowed
citation: U.S. Bureau of Labor Statistics, CPI-U ({series_id}), retrieved {retrieved_at}
```
