-- Baltimore City street centerline segments. Codes kept as published; subtype labels are provisional.
SELECT
    OBJECTID::BIGINT                                                         AS segment_id,
    NULLIF(trim(cline_id::VARCHAR), '')                                      AS cline_id,
    '24510'                                                                  AS county_geoid,
    trim(concat_ws(' ', NULLIF(trim(dirpre), ''), NULLIF(trim(feanme), ''),
                       NULLIF(trim(featype), ''), NULLIF(trim(dirsuf), '')))  AS street_name,
    NULLIF(trim(fr_street), '')                                              AS from_street,
    NULLIF(trim(to_street), '')                                              AS to_street,
    NULLIF(trim(subtype), '')                                                AS subtype_code,
    NULLIF(trim(feat_status), '')                                            AS feature_status,
    NULLIF(trim(sha_class), '')                                              AS sha_functional_class,
    NULLIF(trim(routeid_sha), '')                                            AS sha_route_id,
    NULLIF(trim(id_prefix), '')                                              AS sha_id_prefix,
    NULLIF(trim(id_rte_no::VARCHAR), '')                                     AS sha_route_number,
    ST_Length(ST_Transform(geom, 'OGC:CRS84', 'EPSG:26985'))                 AS length_m,
    to_timestamp(edit_date / 1000)::DATE                                     AS source_edit_date,
    geom                                                                     AS geometry
FROM ST_Read('{raw:baltimore_streets/street_centerline}/features.geojson')
