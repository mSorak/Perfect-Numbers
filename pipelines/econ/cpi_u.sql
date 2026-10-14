-- CPI-U index levels from the BLS API (all requested series, monthly + annual average).
WITH obs AS (
    SELECT s.seriesID AS series_id, unnest(s.data) AS d
    FROM (SELECT unnest(series) AS s
          FROM read_json('{raw:bls/cpi_u}/bls_*.json', format = 'auto', union_by_name = true))
)
SELECT
    series_id,
    CASE series_id
        WHEN 'CUUR0000SA0' THEN 'U.S. city average'
        WHEN 'CUSR0000SA0' THEN 'U.S. city average'
        WHEN 'CUURS35ESA0' THEN 'Baltimore-Columbia-Towson'
    END                                                   AS area,
    series_id[3] = 'S'                                    AS is_seasonally_adjusted,
    d.year::INTEGER                                       AS year,
    d.period                                              AS period,
    CASE WHEN d.period = 'M13' THEN 'annual_average'
         WHEN d.period IN ('S01', 'S02') THEN 'half_year'
         ELSE 'month' END                                 AS period_type,
    CASE WHEN d.period BETWEEN 'M01' AND 'M12'
         THEN make_date(d.year::INTEGER, d.period[2:]::INTEGER, 1) END AS month,
    TRY_CAST(d.value AS DOUBLE)                           AS cpi,
    '1982-84=100'                                         AS base,
    NULLIF(array_to_string(list_filter([f.text FOR f IN d.footnotes], x -> x IS NOT NULL), '; '), '') AS footnotes
FROM obs
