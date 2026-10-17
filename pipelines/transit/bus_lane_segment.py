"""Bus lanes reconciled onto Baltimore City street segments, one row per segment any source flags.

Sources, each matched to segments with pndata.geo.match_lines_to_segments (lanes drawn per side sit a few metres
off the centerline, hence the wider buffer):
- OSM bus-lane tags (transit.bus_lane_existing)
- BCDOT dedicated-bus-lane inventory, 2021 copy (transit.bus_lane_inventory): current vs. recommended
- BCDOT bike layer, facility type 'Shared Bus-Bike Lane' (traffic.bike_facility)
- Proposed East-West Priority Corridor lanes (transit.bus_lane_planned)
"""

from pndata.geo import match_lines_to_segments, to_gdf


def _match(con, segs, sql: str, attrs: list[str], buffer_m: float, min_share: float, max_angle: float):
    lines = to_gdf(con, sql)
    if lines.empty:
        return None
    m = match_lines_to_segments(segs, lines, buffer_m=buffer_m, min_share=min_share, max_angle=max_angle)
    return m.merge(lines[["line_id", *attrs]], on="line_id")


def build(con, ctx):
    p = ctx.card.get("parameters", {})
    kw = dict(buffer_m=p.get("buffer_m", 15), min_share=p.get("min_share", 0.5), max_angle=p.get("max_angle", 30))
    segs = to_gdf(con, """SELECT segment_id, geometry FROM traffic.street_segment
                          WHERE feature_status = 'A' AND coalesce(subtype_code, '') <> 'STRALY' AND length_m > 5""")

    osm = _match(con, segs, """SELECT osm_way_id AS line_id, bus_lane_side, geometry FROM transit.bus_lane_existing""",
                 ["bus_lane_side"], **kw)
    inv = _match(con, segs, """SELECT lane_id AS line_id, is_current, project, hours_open, side, geometry
                               FROM transit.bus_lane_inventory""",
                 ["is_current", "project", "hours_open", "side"], **kw)
    bike = _match(con, segs, """SELECT facility_id AS line_id, geometry FROM traffic.bike_facility
                                WHERE facility_type = 'Shared Bus-Bike Lane'""", [], **kw)
    plan = _match(con, segs, """SELECT lane_id AS line_id, hours, corridor, geometry FROM transit.bus_lane_planned""",
                  ["hours", "corridor"], **kw)

    con.register("_osm", osm.groupby("segment_id").agg(
        osm_side=("bus_lane_side", lambda s: ", ".join(sorted(set(s.dropna()))))).reset_index())
    inv_g = inv.groupby("segment_id").agg(
        inv_current=("is_current", "max"), inv_recommended=("is_current", lambda s: bool((~s.astype(bool)).any())),
        inv_project=("project", lambda s: ", ".join(sorted(set(s.dropna())))),
        inv_hours=("hours_open", lambda s: ", ".join(sorted(set(s.dropna())))),
        inv_side=("side", lambda s: ", ".join(sorted(set(s.dropna()))))).reset_index()
    con.register("_inv", inv_g)
    con.register("_bike", bike[["segment_id"]].drop_duplicates())
    con.register("_plan", plan.groupby("segment_id").agg(
        plan_hours=("hours", lambda s: ", ".join(sorted(set(s.dropna())))),
        plan_corridor=("corridor", lambda s: ", ".join(sorted(set(s.dropna()))))).reset_index())

    return """
    WITH ids AS (SELECT segment_id FROM _osm UNION SELECT segment_id FROM _inv
                 UNION SELECT segment_id FROM _bike UNION SELECT segment_id FROM _plan),
    f AS (
        SELECT ids.segment_id,
               _osm.segment_id IS NOT NULL                       AS on_osm,
               _osm.osm_side,
               coalesce(_inv.inv_current, false)                 AS on_bcdot_inventory,
               coalesce(_inv.inv_recommended, false) AND NOT coalesce(_inv.inv_current, false)
                                                                 AS bcdot_inventory_recommended_only,
               NULLIF(_inv.inv_project, '')                      AS bcdot_inventory_project,
               NULLIF(_inv.inv_hours, '')                        AS bcdot_inventory_hours,
               NULLIF(_inv.inv_side, '')                         AS bcdot_inventory_side,
               _bike.segment_id IS NOT NULL                      AS on_bcdot_bike_layer,
               _plan.segment_id IS NOT NULL                      AS is_proposed_ewpc,
               _plan.plan_hours                                  AS proposed_hours,
               _plan.plan_corridor                               AS proposed_corridor
        FROM ids LEFT JOIN _osm USING (segment_id) LEFT JOIN _inv USING (segment_id)
                 LEFT JOIN _bike USING (segment_id) LEFT JOIN _plan USING (segment_id))
    SELECT f.segment_id, st.street_name, st.length_m,
           CASE WHEN on_osm OR on_bcdot_inventory OR on_bcdot_bike_layer THEN 'existing'
                WHEN is_proposed_ewpc THEN 'proposed'
                WHEN bcdot_inventory_recommended_only THEN 'recommended' END          AS bus_lane_status,
           on_osm::INT + on_bcdot_inventory::INT + on_bcdot_bike_layer::INT          AS n_existing_sources,
           NULLIF(concat_ws('+', CASE WHEN on_bcdot_inventory THEN 'BCDOT inventory' END,
                          CASE WHEN on_bcdot_bike_layer THEN 'BCDOT bike layer' END,
                          CASE WHEN on_osm THEN 'OSM' END), '')                 AS existing_sources,
           f.* EXCLUDE (segment_id),
           st.geometry
    FROM f JOIN traffic.street_segment st USING (segment_id)
    """
