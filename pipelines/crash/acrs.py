"""Staging for MDSP ACRS crash exports: reports, vehicles, persons (occupants + non-motorists), and the
crash-cost model (method 2026.1).

Which snapshots are read is a card parameter, `snapshot_grain`:
  month      → newest snapshot of each YYYY-MM period (tableau_public pulls; current data)
  half_year  → newest snapshot of each YYYYH1/H2 period (legacy UI exports; the published model's inputs)
The same functions build both, so the parity test (tests/test_crash_parity.py) checks the hub's code.
"""

SOURCE = "mdsp_acrs"
SNAP_RE = r"(\d{8}T\d{4}Z__[0-9A-Z-]+)"


def _grain(ctx) -> str:
    return ctx.card.get("parameters", {}).get("snapshot_grain", "month")


def _src(ctx, entity: str, grain: str | None = None, periods: list[str] | None = None) -> str:
    """A relation over the selected snapshots of one entity, with source_snapshot_id/source_period."""
    files = ctx.raw_set(f"{SOURCE}/{entity}", grain or _grain(ctx), periods)
    lst = ", ".join(f"'{f.as_posix()}'" for f in files)
    return f"""(SELECT *, regexp_extract(filename, '{SNAP_RE}', 1) AS source_snapshot_id,
                       split_part(regexp_extract(filename, '{SNAP_RE}', 1), '__', 2) AS source_period
                FROM read_csv([{lst}], all_varchar = true, union_by_name = true, filename = true))"""


def _yn(col: str) -> str:
    return f"CASE \"{col}\" WHEN 'Yes' THEN true WHEN 'No' THEN false END"


def _date(col: str) -> str:
    return f"try_strptime(\"{col}\", '%m/%d/%Y')::DATE"


def acrs_report_sql(src: str) -> str:
    return f"""
        SELECT upper(trim(r.Reportnumber))                     AS report_number,
               {_date('Crashdate')}                             AS crash_date,
               year({_date('Crashdate')})                       AS crash_year,
               NULLIF(r.Crashtime, '')                          AS crash_time,
               TRY_CAST(r.Crashhour AS INTEGER)                 AS crash_hour,
               r.Dayofweek                                      AS day_of_week,
               c.county_geoid,
               r."Crash County"                                 AS acrs_county_code,
               r."Crash County Description"                     AS acrs_county_name,
               TRY_CAST(r."Crash Severity" AS INTEGER)          AS severity_code,
               r."Crash Severity Description"                   AS severity,
               r.AgencyCode                                     AS agency_code,
               r.Agencyname                                     AS agency_name,
               NULLIF(r.RoadName, '')                           AS road_name,
               NULLIF(r."Route Number", '')                     AS route_number,
               r.RouteType                                      AS route_type_code,
               r."RouteType Description"                        AS route_type,
               NULLIF(r.IntersectingRoadName, '')               AS intersecting_road_name,
               r.RoadID                                         AS road_id,
               TRY_CAST(r.MilepointDistance AS DOUBLE)          AS milepoint,
               r.MilepointDirection                             AS milepoint_direction,
               r.FunctionalClass                                AS functional_class_code,
               r."FunctionalClass Description"                  AS functional_class,
               r.CollisionImpact                                AS collision_type_code,
               r."CollisionImpact Description"                  AS collision_type,
               r.FirstHarmEvent                                 AS first_harm_event_code,
               r."FirstHarmEvent Description"                   AS first_harm_event,
               r."Light Description"                            AS light,
               r."Surface Description"                          AS surface,
               r."JunctionRelated Description"                  AS junction,
               {_yn('ImpairedCrash')}                           AS is_impaired,
               {_yn('Motorcycle Crash')}                        AS is_motorcycle,
               {_yn('Non-Motorist Crash')}                      AS is_nonmotorist,
               {_yn('Large Vehicle Involved')}                  AS is_large_vehicle,
               {_yn('Work Zone Related')}                       AS is_work_zone,
               {_yn('Unrestrained Occupants')}                  AS has_unrestrained_occupant,
               TRY_CAST(r.Latitude AS DOUBLE)                   AS latitude,
               TRY_CAST(r.Longitude AS DOUBLE)                  AS longitude,
               CASE WHEN TRY_CAST(r.Latitude AS DOUBLE) BETWEEN 37.8 AND 39.8
                     AND TRY_CAST(r.Longitude AS DOUBLE) BETWEEN -79.6 AND -74.9
                    THEN ST_Point(r.Longitude::DOUBLE, r.Latitude::DOUBLE) END AS geometry,
               r.source_period,
               r.source_snapshot_id
        FROM {src} r
        LEFT JOIN ref.county_codes c ON c.mdot_code::INTEGER = TRY_CAST(r."Crash County" AS INTEGER)"""


def acrs_vehicle_sql(src: str) -> str:
    return f"""
        SELECT upper(trim(v."ReportNumber Veh"))   AS report_number,
               v.VehicleID                         AS vehicle_id,
               TRY_CAST(v."Unitnumber Veh" AS INTEGER) AS unit_number,
               v."BodyType Veh"                    AS body_type_code,
               v."BodyType Veh Description"        AS body_type,
               v."Large Vehicle BodyType Description" AS large_vehicle_body_type,
               NULLIF(v."Make Veh", '')            AS make,
               NULLIF(v."Model Veh", '')           AS model,
               TRY_CAST(v."Year Veh" AS INTEGER)   AS model_year,
               v."Movement Veh Description"        AS movement,
               v."TravelDirection Veh Description" AS travel_direction,
               v."FirstImpact Description"         AS first_impact,
               v."MostHarmfulEvent Veh Description" AS most_harmful_event,
               v."DamageExtent Veh Description"    AS damage_extent,
               v."SpecialFunction Veh Description" AS special_function,
               v."EmergencyUse Veh Description"    AS emergency_use,
               TRY_CAST(v."SpeedLimit Veh" AS INTEGER) AS speed_limit_mph,
               TRY_CAST(v."NumberOfThroughLanes Veh" AS INTEGER) AS through_lanes,
               v."Left Scene Veh"                  AS left_scene,
               v."IsParked"                        AS is_parked_raw,
               v.source_period,
               v.source_snapshot_id
        FROM {src} v"""


def acrs_person_sql(occ: str, nm: str) -> str:
    return f"""
        SELECT upper(trim(o."ReportNumber Occ")) AS report_number,
               o."PersonID Occ"                  AS person_id,
               'occupant'                        AS person_role,
               o."TypeOfOccupant Description"    AS person_type,
               NULLIF(o."VehicleID Occ", '')     AS vehicle_id,
               NULLIF(o."InjuryStatus Occ", '')  AS injury_code,
               o."InjuryStatus Occ Description"  AS injury_status,
               TRY_CAST(o."Age Occ" AS INTEGER)  AS age,
               NULLIF(o."Gender Occ", '')        AS sex,
               o."Restraint Occ Description"     AS restraint,
               o."SeatingLocation Occ Description" AS seating_location,
               o."Ejection Occ Description"      AS ejection,
               o.source_period, o.source_snapshot_id
        FROM {occ} o
        UNION ALL
        SELECT upper(trim(n."ReportNumber NM")), n."PersonID NM", 'nonmotorist', n."Type NM Description",
               NULLIF(n."StruckByVehID NM", ''), NULLIF(n."InjuryStatus NM", ''), n."InjuryStatus NM Description",
               TRY_CAST(n."Age NM" AS INTEGER), NULLIF(n."Gender NM", ''), NULL, n."Location NM Description",
               NULL, n.source_period, n.source_snapshot_id
        FROM {nm} n"""


# ---------- build functions referenced by the cards ----------

def acrs_report(con, ctx):
    return acrs_report_sql(_src(ctx, "reports"))


def acrs_vehicle(con, ctx):
    return acrs_vehicle_sql(_src(ctx, "vehicles"))


def acrs_person(con, ctx):
    return acrs_person_sql(_src(ctx, "occupants"), _src(ctx, "nonmotorists"))


# ---------- crash cost, method 2026.1 ----------

def deflator(con, params: dict) -> tuple[float, str]:
    """Unit-cost multiplier from 2019 to the target dollars, and how it was set."""
    d = params.get("deflator", {})
    if d.get("use_legacy_factor", True):
        return float(d.get("legacy_factor", 1.26)), f"legacy_factor {d.get('legacy_factor', 1.26)} (published model)"
    f = con.sql(f"""SELECT max(cpi) FILTER (WHERE month = DATE '{d['to']}') / max(cpi) FILTER (WHERE month = DATE '{d['from']}')
                    FROM econ.cpi_u WHERE series_id = 'CUUR0000SA0'""").fetchone()[0]
    return float(f), f"CPI-U CUUR0000SA0 {d['to']} / {d['from']}"


COMPONENTS = ["medical", "ems", "market_productivity", "household_productivity", "insurance_admin", "workplace",
              "legal", "congestion", "property_damage", "total_economic", "quality_of_life", "total_comprehensive"]


def report_cost_sql(reports: str, vehicles: str, persons: str, factor: float, factor_method: str,
                    usd_year: int, map_version: str = "v1") -> str:
    """Per report: PDO crashes (severity 3) cost n_vehicles × PDOVehicle; others cost Σ persons × the unit
    cost of their injury level (ACRS → MAIS map). Persons with no injury status cost nothing (as published)."""
    unit = lambda comp: f"max(u.unit_cost_usd2019) FILTER (WHERE u.cost_component = '{comp}')"
    comp_cols = ",\n".join(
        f"""   CASE WHEN r.severity_code = 3 THEN coalesce(v.n_vehicles, 0) * pdo.{c}
                    ELSE coalesce(p.{c}, 0) END * {factor} AS {c}_usd{usd_year}""" for c in COMPONENTS)
    return f"""
        WITH unit AS (
            SELECT u.injury_level, {', '.join(f'{unit(c)} AS {c}' for c in COMPONENTS)}
            FROM ref.nhtsa_unit_cost_2019 u GROUP BY u.injury_level),
        pdo AS (FROM unit WHERE injury_level = 'PDOVehicle'),
        v AS (SELECT report_number, count(*) AS n_vehicles FROM {vehicles} GROUP BY ALL),
        p AS (
            SELECT ps.report_number,
                   count(*) AS n_persons,
                   count(*) FILTER (WHERE ps.injury_code IS NULL) AS n_persons_no_injury_status,
                   count(*) FILTER (WHERE m.injury_level = 'Fatal') AS n_fatal,
                   count(*) FILTER (WHERE ps.injury_code = '02') AS n_serious_injury,
                   {', '.join(f'sum(un.{c}) AS {c}' for c in COMPONENTS)}
            FROM {persons} ps
            LEFT JOIN ref.acrs_injury_to_mais m ON m.map_version = '{map_version}' AND m.acrs_injury_code = ps.injury_code
            LEFT JOIN unit un ON un.injury_level = m.injury_level
            GROUP BY ps.report_number)
        SELECT r.report_number, r.crash_date, r.crash_year, r.county_geoid, r.severity_code, r.severity,
               coalesce(v.n_vehicles, 0) AS n_vehicles,
               coalesce(p.n_persons, 0) AS n_persons,
               coalesce(p.n_persons_no_injury_status, 0) AS n_persons_no_injury_status,
               coalesce(p.n_fatal, 0) AS n_fatal,
               coalesce(p.n_serious_injury, 0) AS n_serious_injury,
{comp_cols},
               '2026.1' AS method_version,
               '{map_version}' AS injury_map_version,
               {factor}::DOUBLE AS deflator,
               '{factor_method}' AS deflator_method,
               r.source_period
        FROM {reports} r
        LEFT JOIN v USING (report_number)
        LEFT JOIN p USING (report_number)
        CROSS JOIN pdo"""


def report_cost(con, ctx):
    params = ctx.card.get("parameters", {})
    factor, how = deflator(con, params)
    return report_cost_sql("crash.acrs_report", "crash.acrs_vehicle", "crash.acrs_person", factor, how,
                           int(params.get("usd_year", 2025)))


# ---------- geography ----------

def report_geo_sql(reports: str) -> str:
    """Point-in-polygon county and tract (TIGER 2024 polygons, which include water). 'Intersects', so a point
    exactly on a boundary still gets a unit; ties go to the lowest GEOID. Points outside every Maryland
    polygon get null. The published model used shoreline-clipped NHGIS shapes, so it left crashes on
    bridges/tunnels/water unassigned (see tests/test_crash_parity.py)."""
    return f"""
        WITH pts AS (SELECT report_number, county_geoid AS acrs_county_geoid, geometry FROM {reports}),
        cty AS (SELECT p.report_number, min(c.geoid) AS county_geoid, count(*) AS n
                FROM pts p JOIN geo.county c ON ST_Intersects(p.geometry, c.geometry) GROUP BY 1),
        trt AS (SELECT p.report_number, min(t.geoid) AS tract_geoid
                FROM pts p JOIN geo.tract t ON ST_Intersects(p.geometry, t.geometry) GROUP BY 1)
        SELECT p.report_number,
               cty.county_geoid,
               trt.tract_geoid,
               2024 AS geoid_vintage,
               p.acrs_county_geoid,
               cty.county_geoid IS DISTINCT FROM p.acrs_county_geoid AS county_differs_from_acrs,
               p.geometry IS NOT NULL AS has_point
        FROM pts p LEFT JOIN cty USING (report_number) LEFT JOIN trt USING (report_number)"""


def report_geo(con, ctx):
    return report_geo_sql("crash.acrs_report")
