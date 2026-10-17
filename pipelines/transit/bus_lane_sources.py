"""Staging for the bus-lane layers from source bcdot_bus_lanes (consultant-hosted BCDOT/MTA layers).

Codes are kept as published; blank strings become NULL. Lengths are measured in EPSG:26985.
"""


def _src(ctx, key: str) -> tuple[str, str]:
    path = (ctx.raw(key) / "features.geojson").as_posix()
    return f"ST_Read('{path}')", ctx.raw_inputs[key]["snapshot_id"]


def _blank(col: str) -> str:
    return f"NULLIF(trim({col}::VARCHAR), '')"


LENGTH = "ST_Length(ST_Transform(geom, 'OGC:CRS84', 'EPSG:26985'))"


def inventory(con, ctx):
    """BCDOT dedicated-bus-lane inventory (2021 copy hosted by Mead & Hunt)."""
    src, snap = _src(ctx, "bcdot_bus_lanes/bus_lane_2021")
    return f"""
    SELECT OBJECTID::BIGINT                         AS lane_id,
           GIS_ID::VARCHAR                          AS gis_id,
           {_blank('ST_ID')}                        AS city_street_id,
           {_blank('ST_NAME')}                      AS street_name,
           {_blank('BLOCKTEXT')}                    AS block_text,
           {_blank('FROM_ST')}                      AS from_street,
           {_blank('TO_ST')}                        AS to_street,
           DBL_Type                                 AS inventory_status,
           DBL_Type = 'Current/Under Construction'  AS is_current,
           {_blank('FAC_TYPE1')}                    AS facility_type,
           {_blank('STATUS1')}                      AS status_code,
           {_blank('ONEWAY1')}                      AS oneway,
           {_blank('FAC_SIDE')}                     AS side,
           LANECOUNT::INT                           AS lane_count,
           {_blank('PROJECT')}                      AS project,
           {_blank('OWNER')}                        AS owner,
           {_blank('HRS_OPEN')}                     AS hours_open,
           {LENGTH}                                 AS length_m,
           '{snap}'                                 AS source_snapshot_id,
           geom                                     AS geometry
    FROM {src}"""


def planned(con, ctx):
    """East-West Priority Corridor proposed dedicated bus lanes (Oct 2024 design update)."""
    src, snap = _src(ctx, "bcdot_bus_lanes/ewpc_proposed_2024")
    return f"""
    SELECT FID::BIGINT                              AS lane_id,
           {_blank('Corridor')}                     AS corridor,
           {_blank('Name')}                         AS extent,
           {_blank('Type')}                         AS lane_type,
           {_blank('Type2')}                        AS lane_type_group,
           lower({_blank('NorthSouth')})            AS travel_direction,
           CASE WHEN Type2 ILIKE '%24/7%' THEN '24/7'
                WHEN Type2 ILIKE '%peak%' THEN 'peak period' END AS hours,
           'proposed'                               AS status,
           {LENGTH}                                 AS length_m,
           '{snap}'                                 AS source_snapshot_id,
           geom                                     AS geometry
    FROM {src}"""
