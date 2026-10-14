-- TIGER/Line 2024 counties, filtered to Maryland. NAD83 coordinates relabelled as CRS84 (<2 m difference).
SELECT
    GEOID                         AS geoid,
    2024                          AS geoid_vintage,
    STATEFP                       AS statefp,
    COUNTYFP                      AS countyfp,
    NAME                          AS name,
    NAMELSAD                      AS name_full,
    ALAND::BIGINT                 AS aland_m2,
    AWATER::BIGINT                AS awater_m2,
    ST_SetCRS(geom, 'OGC:CRS84')  AS geometry
FROM ST_Read('/vsizip/{raw:census_tiger/county_us_2024}/tl_2024_us_county.zip')
WHERE STATEFP = '24'
