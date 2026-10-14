"""Staging for MTA local-bus GTFS tables. One function per dataset; all read the latest feed snapshot."""

RAW = "mta_gtfs/local_bus"


def _csv(ctx, name: str) -> str:
    return f"read_csv('{(ctx.raw(RAW) / 'extracted' / name).as_posix()}', all_varchar=true, header=true)"


def _feed(ctx) -> str:
    ctx.raw(RAW)
    rec = ctx.raw_inputs[RAW]
    return f"'{rec['snapshot_id']}' AS feed_snapshot_id"


def _secs(col: str) -> str:
    # GTFS times can exceed 24:00:00 for trips past midnight
    return (f"(split_part({col}, ':', 1)::INT * 3600 + split_part({col}, ':', 2)::INT * 60 "
            f"+ split_part({col}, ':', 3)::INT)")


def feed(con, ctx):
    return f"""SELECT feed_version, strptime(feed_start_date, '%Y%m%d')::DATE AS feed_start_date,
                      strptime(feed_end_date, '%Y%m%d')::DATE AS feed_end_date, feed_publisher_name AS publisher,
                      {_feed(ctx)} FROM {_csv(ctx, 'feed_info.txt')}"""


def route(con, ctx):
    return f"""SELECT route_id, route_short_name, route_long_name, route_type::INT AS route_type,
                      NULLIF(route_color, '') AS route_color, NULLIF(network_id, '') AS network_id, {_feed(ctx)}
               FROM {_csv(ctx, 'routes.txt')}"""


def trip(con, ctx):
    return f"""SELECT trip_id, route_id, service_id, direction_id::INT AS direction_id, shape_id,
                      trip_headsign AS headsign, NULLIF(block_id, '') AS block_id, {_feed(ctx)}
               FROM {_csv(ctx, 'trips.txt')}"""


def stop(con, ctx):
    return f"""SELECT stop_id, NULLIF(stop_code, '') AS stop_code, stop_name,
                      stop_lat::DOUBLE AS stop_lat, stop_lon::DOUBLE AS stop_lon,
                      NULLIF(direction, '') AS direction, NULLIF(position, '') AS position,
                      ST_Point(stop_lon::DOUBLE, stop_lat::DOUBLE)::GEOMETRY('OGC:CRS84') AS geometry, {_feed(ctx)}
               FROM {_csv(ctx, 'stops.txt')}"""


def stop_time(con, ctx):
    return f"""SELECT trip_id, stop_id, stop_sequence::INT AS stop_sequence,
                      {_secs('arrival_time')} AS arrival_s, {_secs('departure_time')} AS departure_s,
                      TRY_CAST(NULLIF(shape_dist_traveled, '') AS DOUBLE) AS shape_dist_traveled,
                      pickup_type::INT AS pickup_type, drop_off_type::INT AS drop_off_type,
                      timepoint::INT AS timepoint
               FROM {_csv(ctx, 'stop_times.txt')}"""


def shape(con, ctx):
    return f"""SELECT shape_id,
                      ST_MakeLine(list(ST_Point(shape_pt_lon::DOUBLE, shape_pt_lat::DOUBLE)
                                       ORDER BY shape_pt_sequence::INT))::GEOMETRY('OGC:CRS84') AS geometry,
                      count(*) AS n_points, {_feed(ctx)}
               FROM {_csv(ctx, 'shapes.txt')} GROUP BY shape_id"""


def service_date(con, ctx):
    """Every (date, service_id) the feed operates, from calendar.txt plus calendar_dates.txt exceptions."""
    return f"""
    WITH cal AS (FROM {_csv(ctx, 'calendar.txt')}),
    days AS (
        SELECT service_id, d::DATE AS date
        FROM cal, range(strptime(start_date, '%Y%m%d'), strptime(end_date, '%Y%m%d') + INTERVAL 1 DAY, INTERVAL 1 DAY) t(d)
        WHERE CASE dayofweek(d) WHEN 0 THEN sunday WHEN 1 THEN monday WHEN 2 THEN tuesday WHEN 3 THEN wednesday
                                WHEN 4 THEN thursday WHEN 5 THEN friday ELSE saturday END = '1'),
    ex AS (SELECT service_id, strptime(date, '%Y%m%d')::DATE AS date, exception_type FROM {_csv(ctx, 'calendar_dates.txt')})
    SELECT d.service_id, d.date FROM days d
    WHERE NOT EXISTS (SELECT 1 FROM ex WHERE ex.service_id = d.service_id AND ex.date = d.date AND ex.exception_type = '2')
    UNION
    SELECT service_id, date FROM ex WHERE exception_type = '1'"""
