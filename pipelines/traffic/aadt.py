"""MDOT SHA AADT: segment geometry/attributes, and segment × year volumes with explicit years.

The unsuffixed AADT/AAWDT columns are the release's newest year, which has no suffix. Its year is
inferred as (newest AADT_<year> column) + 1 for each snapshot, and recorded in `year_method`.
"""

import re

ENTITY = "mdot_sha_aadt/aadt_segment"


def _src(ctx):
    p = (ctx.raw(ENTITY) / "features.geojson").as_posix()
    return f"ST_Read('{p}')", ctx.raw_inputs[ENTITY]["snapshot_id"]


def _years(con, src):
    cols = [r[0] for r in con.sql(f"DESCRIBE SELECT * FROM {src}").fetchall()]
    hist = sorted(int(m[1]) for c in cols if (m := re.fullmatch(r"AADT_(\d{4})", c)))
    return hist, hist[-1] + 1


def aadt_segment(con, ctx):
    src, snap = _src(ctx)
    _, current = _years(con, src)
    return f"""
        SELECT s.GlobalID                          AS segment_id,
               s.LOCATION_ID::VARCHAR              AS location_id,
               c.county_geoid,
               s.COUNTY_ID::INTEGER                AS mdot_county_code,
               NULLIF(trim(s.MUNICIPALITY), '')    AS municipality,
               s.ROADNAME                          AS road_name,
               s.ID_PREFIX                         AS id_prefix,
               s.ID_RTE_NO::VARCHAR                AS route_number,
               s.ROUTEID_RH                        AS route_id_rh,
               s.ROAD_SECTION                      AS road_section,
               s.BEGIN_SECTION::DOUBLE             AS begin_mp,
               s.END_SECTION::DOUBLE               AS end_mp,
               s.STATION_DESC                      AS station_desc,
               s.RURAL_URBAN                       AS rural_urban,
               s.F_SYSTEM::INTEGER                 AS f_system,
               s.F_SYSTEM_DESC                     AS f_system_desc,
               s.MAIN_LINE                         AS main_line,
               s.NUM_LANES::INTEGER                AS num_lanes,
               s.COUNTED_FACTORED                  AS counted_factored_latest,
               {current}                           AS latest_year,
               ST_Length(ST_Transform(s.geom, 'OGC:CRS84', 'EPSG:26985')) AS length_m,
               '{snap}'                            AS source_snapshot_id,
               s.geom                              AS geometry
        FROM {src} s
        LEFT JOIN ref.county_codes c ON c.mdot_code::INTEGER = s.COUNTY_ID::INTEGER"""


def aadt_segment_year(con, ctx):
    src, snap = _src(ctx)
    hist, current = _years(con, src)
    parts = [f"SELECT GlobalID, {y} AS year, AADT_{y} AS aadt, AAWDT_{y} AS aawdt, false AS is_latest_column FROM {src}"
             for y in hist]
    parts.append(f"SELECT GlobalID, {current}, AADT, AAWDT, true FROM {src}")
    method = f"latest column year inferred as max(AADT_<year>)+1 = {current}"
    return f"""
        WITH long AS ({' UNION ALL '.join(parts)})
        SELECT l.GlobalID AS segment_id, l.year,
               NULLIF(l.aadt::BIGINT, 0)  AS aadt,
               NULLIF(l.aawdt::BIGINT, 0) AS aawdt,
               l.is_latest_column,
               CASE WHEN l.is_latest_column THEN '{method}' ELSE 'AADT_<year> column' END AS year_method,
               g.length_m,
               NULLIF(l.aadt::BIGINT, 0) * g.length_m / 1609.344 AS daily_vmt,
               NULLIF(l.aadt::BIGINT, 0) * g.length_m / 1609.344
                   * (CASE WHEN l.year % 4 = 0 THEN 366 ELSE 365 END) AS annual_vmt,
               '{snap}' AS source_snapshot_id
        FROM long l
        JOIN (SELECT GlobalID, ST_Length(ST_Transform(geom, 'OGC:CRS84', 'EPSG:26985')) AS length_m FROM {src}) g
          USING (GlobalID)
        WHERE l.aadt IS NOT NULL AND l.aadt::BIGINT > 0"""
