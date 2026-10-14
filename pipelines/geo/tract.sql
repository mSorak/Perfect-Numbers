-- TIGER/Line 2024 census tracts for Maryland (2020 tract definitions).
SELECT
    GEOID                         AS geoid,
    2024                          AS geoid_vintage,
    STATEFP || COUNTYFP           AS county_geoid,
    TRACTCE                       AS tractce,
    NAMELSAD                      AS name_full,
    ALAND::BIGINT                 AS aland_m2,
    AWATER::BIGINT                AS awater_m2,
    ST_SetCRS(geom, 'OGC:CRS84')  AS geometry
FROM ST_Read('/vsizip/{raw:census_tiger/tract_md_2024}/tl_2024_24_tract.zip')
