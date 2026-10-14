-- MDOT SHA roadway maintenance responsibility, Baltimore City and Baltimore County.
SELECT
    GlobalID                                      AS section_id,
    CASE COUNTY WHEN 24 THEN '24510' WHEN 3 THEN '24005' END AS county_geoid,
    COUNTY::INTEGER                               AS mdot_county_code,
    ROAD_NAME                                     AS road_name,
    ID_PREFIX                                     AS id_prefix,
    ID_RTE_NO::VARCHAR                            AS route_number,
    ROUTEID_RH                                    AS route_id_rh,
    FROM_MEASURE::DOUBLE                          AS from_measure_mi,
    TO_MEASURE::DOUBLE                            AS to_measure_mi,
    GOVT_CONTROL                                  AS govt_control_code,
    MAINTENANCE_RESPONSIBLITY                     AS maintenance_responsibility,
    CASE
        WHEN MAINTENANCE_RESPONSIBLITY ILIKE 'STATE HIGHWAY%' THEN 'MDOT SHA'
        WHEN MAINTENANCE_RESPONSIBLITY ILIKE 'STATE TOLL%'    THEN 'MDTA (state toll)'
        WHEN MAINTENANCE_RESPONSIBLITY ILIKE 'COUNTY%'        THEN 'County'
        WHEN MAINTENANCE_RESPONSIBLITY ILIKE 'CITY OR MUNIC%' THEN 'City/municipal'
        WHEN MAINTENANCE_RESPONSIBLITY ILIKE '%FEDERAL%'
          OR MAINTENANCE_RESPONSIBLITY ILIKE '%PARK SERVICE%' THEN 'Federal'
        ELSE 'Other'
    END                                           AS maintainer_group,
    MAIN_LINE                                     AS main_line,
    NULLIF(trim(MUNICIPALITY_NAME), '')           AS municipality,
    ST_Length(ST_Transform(geom, 'OGC:CRS84', 'EPSG:26985')) AS length_m,
    geom                                          AS geometry
FROM ST_Read('{raw:mdot_sha_roads/maintenance_responsibility}/features.geojson')
