SELECT
    OBJECTID::BIGINT          AS facility_id,
    GIS_ID::VARCHAR           AS gis_id,
    ST_NAME                   AS street_name,
    FROM_ST                   AS from_street,
    TO_ST                     AS to_street,
    FAC_TYPE1                 AS facility_type,
    STATUS1                   AS status,
    FAC_TYPE2                 AS facility_type_2,
    STATUS2                   AS status_2,
    ONEWAY1                   AS oneway,
    FAC_SIDE                  AS side,
    INST_YR::VARCHAR          AS install_year,
    OWNER                     AS owner,
    ST_Length(ST_Transform(geom, 'OGC:CRS84', 'EPSG:26985')) AS length_m,
    geom                      AS geometry
FROM ST_Read('{raw:baltimore_streets/bike_facilities}/features.geojson')
