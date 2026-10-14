"""Geometry helpers shared by pipelines: load metric GeoDataFrames and match lines to street segments."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

MEASURE_CRS = "EPSG:26985"  # NAD83 / Maryland, metres


def to_gdf(con, sql: str, geometry: str = "geometry", crs: str = MEASURE_CRS) -> gpd.GeoDataFrame:
    """Run SQL returning a CRS84 geometry column; return a GeoDataFrame projected to `crs`."""
    df = con.sql(f"SELECT * REPLACE (ST_AsWKB({geometry}) AS {geometry}) FROM ({sql})").df()
    geom = shapely.from_wkb(df.pop(geometry).map(bytes).to_numpy())
    return gpd.GeoDataFrame(df, geometry=geom, crs="OGC:CRS84").to_crs(crs)


def _bearing(p1, p2) -> np.ndarray:
    dx = shapely.get_x(p2) - shapely.get_x(p1)
    dy = shapely.get_y(p2) - shapely.get_y(p1)
    return np.degrees(np.arctan2(dx, dy)) % 360


def match_lines_to_segments(segments: gpd.GeoDataFrame, lines: gpd.GeoDataFrame, *, buffer_m: float = 15,
                            min_share: float = 0.6, max_angle: float = 30, seg_id: str = "segment_id",
                            line_id: str = "line_id") -> pd.DataFrame:
    """Find segments that run *along* a line (not just across it).

    A segment matches a line when at least `min_share` of its length lies within `buffer_m` of the line AND its
    bearing is within `max_angle` degrees of the line's local bearing (either direction). Returns one row per
    match with: seg_id, line_id, share, angle_diff, same_direction (segment digitized the same way the line
    runs) and position (0–1 fraction along the line at the segment's midpoint).
    """
    segments = segments.reset_index(drop=True)  # positional alignment below assumes a clean index
    lines = lines.reset_index(drop=True)
    buf = gpd.GeoDataFrame({line_id: lines[line_id].to_numpy()}, geometry=lines.geometry.buffer(buffer_m).to_numpy(),
                           crs=lines.crs)
    pairs = gpd.sjoin(segments[[seg_id, "geometry"]], buf, predicate="intersects", how="inner")
    if pairs.empty:
        return pd.DataFrame(columns=[seg_id, line_id, "share", "angle_diff", "same_direction", "position"])
    seg_geom = segments.set_index(seg_id).geometry.loc[pairs[seg_id]].to_numpy()
    line_geom = lines.set_index(line_id).geometry.loc[pairs[line_id]].to_numpy()
    buf_geom = buf.set_index(line_id).geometry.loc[pairs[line_id]].to_numpy()

    seg_len = shapely.length(seg_geom)
    share = shapely.length(shapely.intersection(seg_geom, buf_geom)) / np.where(seg_len > 0, seg_len, np.nan)

    start = shapely.get_point(shapely.line_merge(seg_geom), 0)
    end = shapely.get_point(shapely.line_merge(seg_geom), -1)
    mid = shapely.line_interpolate_point(seg_geom, 0.5, normalized=True)
    seg_bearing = _bearing(start, end)

    merged = shapely.line_merge(line_geom)
    d = shapely.line_locate_point(merged, mid)
    total = shapely.length(merged)
    p1 = shapely.line_interpolate_point(merged, np.clip(d - 10, 0, None))
    p2 = shapely.line_interpolate_point(merged, np.minimum(d + 10, total))
    line_bearing = _bearing(p1, p2)
    diff = np.abs((seg_bearing - line_bearing + 180) % 360 - 180)  # 0..180
    aligned = np.minimum(diff, 180 - diff)                          # 0..90, direction-agnostic

    out = pd.DataFrame({seg_id: pairs[seg_id].to_numpy(), line_id: pairs[line_id].to_numpy(),
                        "share": share, "angle_diff": aligned, "same_direction": diff < 90,
                        "position": np.where(total > 0, d / total, np.nan)})
    return out[(out["share"] >= min_share) & (out["angle_diff"] <= max_angle)].reset_index(drop=True)
