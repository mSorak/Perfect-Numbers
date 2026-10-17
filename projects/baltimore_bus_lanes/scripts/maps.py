"""Draft maps for the Baltimore bus piece. Reads the hub by dataset ID; writes PNGs to ../outputs/.

Run from the repo root:
    uv run --with matplotlib python projects/baltimore_bus_lanes/scripts/maps.py

Styling follows the dataviz skill: ordinal single-hue blue ramp for magnitude (validated, light→dark),
binned classes with a legend, recessive grey street base, text in ink colours, red reserved for bus lanes.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import pndata as pn  # noqa: E402
from pndata.geo import to_gdf  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import riders  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "outputs"
CRS = "EPSG:26985"

# Tokens (reference palette, light mode)
SURFACE, INK, INK2, MUTED, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#dcdbd6"
RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]          # ordinal, validated
WIDTH = [0.7, 1.0, 1.4, 1.9, 2.6]
LANE_RED = "#e34948"
CATS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]           # categorical, validated (order fixed)
DOWNTOWN_LONLAT = (-76.6330, -76.5920, 39.2780, 39.3080)  # Mt Vernon / Penn Station edge to Inner Harbor / Harbor East


def _downtown_extent():
    from pyproj import Transformer
    t = Transformer.from_crs("OGC:CRS84", CRS, always_xy=True)
    x0, y0 = t.transform(DOWNTOWN_LONLAT[0], DOWNTOWN_LONLAT[2])
    x1, y1 = t.transform(DOWNTOWN_LONLAT[1], DOWNTOWN_LONLAT[3])
    return (x0, x1, y0, y1)


DOWNTOWN = _downtown_extent()

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
                     "axes.edgecolor": BASE, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})


def load(con):
    base = to_gdf(con, """SELECT geometry FROM traffic.street_segment
                          WHERE feature_status = 'A' AND coalesce(subtype_code, '') <> 'STRALY'""")
    city = to_gdf(con, "SELECT geometry FROM geo.county WHERE geoid = '24510'")
    seg = to_gdf(con, "FROM transit.bus_segment_summary")
    lanes = to_gdf(con, "FROM transit.bus_lane_segment")
    mta = con.sql("SELECT feed_version, feed_start_date, feed_end_date, feed_snapshot_id FROM transit.gtfs_feed").fetchone()
    ccc_snap = con.sql("SELECT any_value(feed_snapshot_id) FROM transit.ccc_gtfs_route").fetchone()[0]
    feeds = (f"MTA local-bus GTFS v{mta[0]} (valid {mta[1]:%Y-%m-%d} to {mta[2]:%Y-%m-%d}, snapshot {mta[3]})"
             f"; Charm City Circulator GTFS via TripShot (snapshot {ccc_snap})")
    return base, city, seg, lanes, feeds


def _class(values, breaks):
    import numpy as np
    return np.digitize(values, breaks[1:-1], right=False)


def _frame(ax, city, base, extent=None):
    base.plot(ax=ax, color=BASE, linewidth=0.25 if extent is None else 0.5, zorder=1)
    city.boundary.plot(ax=ax, color=MUTED, linewidth=0.6, zorder=0)
    if extent:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
    else:
        xmin, ymin, xmax, ymax = city.total_bounds
        ax.set_xlim(xmin - 300, xmax + 300)
        ax.set_ylim(ymin - 300, ymax + 300)
    ax.set_axis_off()
    ax.set_aspect("equal")


def _downtown_box(ax):
    x0, x1, y0, y1 = DOWNTOWN
    ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=INK2, linewidth=0.8, zorder=6)
    ax.annotate("Downtown →", (x1, y1), xytext=(4, 2), textcoords="offset points", color=INK2, fontsize=8)


def _figure(title, subtitle, footer):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 7.4), gridspec_kw={"width_ratios": [1.05, 1]})
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.12, wspace=0.03)
    fig.text(0.02, 0.955, title, fontsize=15, weight="bold", color=INK)
    fig.text(0.02, 0.915, subtitle, fontsize=10, color=INK2)
    wrapped = "\n".join(textwrap.fill(par, 200) for par in footer.split("\n"))
    fig.text(0.02, 0.015, wrapped, fontsize=7.2, color=INK2, va="bottom")
    fig.text(0.98, 0.955, "DRAFT", fontsize=10, color=MUTED, ha="right", weight="bold")
    return fig, a1, a2


def _draw_classes(ax, gdf, col, breaks, scale=1.0):
    g = gdf[gdf[col] > 0].sort_values(col).copy()
    g["cls"] = _class(g[col].to_numpy(), breaks)
    for c in range(len(breaks) - 1):
        sub = g[g["cls"] == c]
        if not sub.empty:
            sub.plot(ax=ax, color=RAMP[c], linewidth=WIDTH[c] * scale, zorder=3 + c, capstyle="round")


def _legend(ax, breaks, unit, extra=()):
    labels = [f"{breaks[i]:,g}–{breaks[i + 1] - 1:,g}" if i < len(breaks) - 2 else f"{breaks[i]:,g}+"
              for i in range(len(breaks) - 1)]
    handles = [Line2D([], [], color=RAMP[i], linewidth=WIDTH[i] * 1.6, label=labels[i]) for i in range(len(labels))]
    leg = ax.legend(handles=[*handles, *extra], title=unit, loc="lower left", frameon=False, fontsize=8,
                    title_fontsize=8.5, labelcolor=INK)
    leg.get_title().set_color(INK2)


def frequency_map(base, city, seg, feeds, col, fname, title, subtitle, window, operators):
    breaks = [0.5, 3.5, 7.5, 11.5, 19.5, 1000]   # buses per hour, busier direction: 1–3, 4–7, 8–11, 12–19, 20+
    footer = (f"Scheduled service, Wednesday 2026-10-14 ({window}); busier direction. Operators: {operators}. "
              f"Feeds: {feeds}.\nStreet segments are Baltimore City centerlines; a route is matched to the streets it runs "
              "along. Short segments at Mondawmin and State Center reflect station convergence. "
              "Sources: MDOT MTA, Baltimore City DOT, Baltimore City EGIS. Perfect Numbers hub, transit.bus_segment_summary.")
    fig, a1, a2 = _figure(title, subtitle, footer)
    for ax, ext, sc in ((a1, None, 1.0), (a2, DOWNTOWN, 1.8)):
        _frame(ax, city, base, ext)
        _draw_classes(ax, seg, col, breaks, sc)
    _downtown_box(a1)
    _legend(a1, [1, 4, 8, 12, 20, 1000], "Buses per hour")
    fig.savefig(OUT / fname, dpi=160)
    plt.close(fig)


def riders_map(base, city, seg, lanes, est, diag, feeds, fname):
    g = seg.merge(est, on="segment_id", how="left").fillna({"riders_v1_max_direction": 0})
    breaks = [1, 250, 500, 1000, 2000, 100000]
    existing = lanes[lanes["bus_lane_status"] == "existing"]
    proposed = lanes[lanes["bus_lane_status"] == "proposed"]
    footer = (f"ESTIMATE ({diag['method']}): stop boardings/alightings ({diag['stop_ridership_season']}) allocated to MTA "
              f"route patterns by scheduled trips and accumulated along each route, scaled to each route's average weekday "
              f"riders ({diag['route_riders_window']}, MTA Customer Experience dashboard). Busier direction. Circulator not "
              "included (no route or stop counts).\n"
              f"Service pattern: Wednesday 2026-10-14. Feeds: {feeds}. Bus lanes: union of BCDOT inventory (2021), "
              "BCDOT bike layer and OpenStreetMap (2026-10-17); proposed = MTA East-West corridor design (Oct 2024).")
    fig, a1, a2 = _figure("Where bus riders are, and where the bus lanes are",
                          "Estimated weekday MTA bus riders passing each street segment, busier direction",
                          footer)
    for ax, ext, sc in ((a1, None, 1.0), (a2, DOWNTOWN, 1.8)):
        _frame(ax, city, base, ext)
        existing.plot(ax=ax, color=LANE_RED, linewidth=4.2 * sc, zorder=2, alpha=0.9, capstyle="round")
        proposed.plot(ax=ax, color=LANE_RED, linewidth=4.2 * sc, zorder=2, linestyle=(0, (1.2, 1.0)), alpha=0.9)
        _draw_classes(ax, g, "riders_v1_max_direction", breaks, sc)
    _downtown_box(a1)
    extra = [Line2D([], [], color=LANE_RED, linewidth=5, label="Bus lane (existing)"),
             Line2D([], [], color=LANE_RED, linewidth=5, linestyle=(0, (1.2, 1.0)), label="Bus lane (proposed, East-West corridor)")]
    _legend(a1, breaks, "Est. weekday riders (v1)", extra)
    fig.savefig(OUT / fname, dpi=160)
    plt.close(fig)


def lanes_map(base, city, lanes, fname):
    l = lanes.copy()
    l["cat"] = l["existing_sources"].fillna("")
    cats = [
        ("Existing: BCDOT and OSM agree", lambda d: d["on_osm"] & (d["on_bcdot_inventory"] | d["on_bcdot_bike_layer"]), "-"),
        ("Existing: BCDOT only", lambda d: ~d["on_osm"] & (d["on_bcdot_inventory"] | d["on_bcdot_bike_layer"]), "-"),
        ("Existing: OSM only", lambda d: d["on_osm"] & ~(d["on_bcdot_inventory"] | d["on_bcdot_bike_layer"]), "-"),
        ("Proposed (East-West corridor, 2024)", lambda d: d["bus_lane_status"] == "proposed", (0, (3, 1.5))),
        ("Recommended (BCDOT 2021, not built)", lambda d: d["bus_lane_status"] == "recommended", (0, (1, 1.2))),
    ]
    footer = ("Sources: BCDOT dedicated-bus-lane inventory (BCDOT schema, consultant-hosted copy last edited 2021-11); "
              "BCDOT bike-facility layer ('Shared Bus-Bike Lane'); OpenStreetMap bus-lane tags (Overpass 2026-10-17, "
              "© OpenStreetMap contributors); MTA East-West Priority Corridor proposed lanes (Oct 2024 update).\n"
              "Each source is matched to the city street centerline it runs along; a lane on either side flags the segment. "
              "Perfect Numbers hub, transit.bus_lane_segment.")
    fig, a1, a2 = _figure("Baltimore's bus lanes: what each source says",
                          "Street segments with a bus lane by source, plus proposed and recommended lanes", footer)
    handles = []
    for (label, f, ls), color in zip(cats, CATS):
        sub = l[f(l)]
        for ax, sc in ((a1, 1.0), (a2, 1.8)):
            if not sub.empty:
                sub.plot(ax=ax, color=color, linewidth=2.2 * sc, linestyle=ls, zorder=3)
        km = sub["length_m"].sum() / 1000
        handles.append(Line2D([], [], color=color, linewidth=3, linestyle=ls, label=f"{label} — {km:.1f} km"))
    _frame(a1, city, base)
    _frame(a2, city, base, DOWNTOWN)
    _downtown_box(a1)
    leg = a1.legend(handles=handles, loc="lower left", frameon=False, fontsize=8, title="Centerline km",
                    title_fontsize=8.5, labelcolor=INK)
    leg.get_title().set_color(INK2)
    fig.savefig(OUT / fname, dpi=160)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    con = pn.connect()
    base, city, seg, lanes, feeds = load(con)
    mta_only, both = "MTA local bus", "MTA local bus + Charm City Circulator"
    specs = [
        ("peak_hour_buses_per_hour", "m1_peak_hour_mta.png", "Buses per hour at the busiest hour: MTA",
         "Weekday buses in each street's busiest clock hour, busier direction", "busiest clock hour", mta_only),
        ("peak_hour_buses_per_hour_all", "m2_peak_hour_all.png", "Buses per hour at the busiest hour: MTA + Circulator",
         "Weekday buses in each street's busiest clock hour, busier direction", "busiest clock hour", both),
        ("midday_buses_per_hour", "m3a_midday_mta.png", "Midday buses per hour: MTA",
         "Weekday 9 am–3 pm average, busier direction", "9 am–3 pm average", mta_only),
        ("midday_buses_per_hour_all", "m3b_midday_all.png", "Midday buses per hour: MTA + Circulator",
         "Weekday 9 am–3 pm average, busier direction", "9 am–3 pm average", both),
        ("daytime_buses_per_hour", "m4a_daytime_mta.png", "All-day buses per hour: MTA",
         "Weekday 6 am–7 pm average, busier direction", "6 am–7 pm average", mta_only),
        ("daytime_buses_per_hour_all", "m4b_daytime_all.png", "All-day buses per hour: MTA + Circulator",
         "Weekday 6 am–7 pm average, busier direction", "6 am–7 pm average", both),
    ]
    for col, fname, title, sub, window, ops in specs:
        frequency_map(base, city, seg, feeds, col, fname, title, sub, window, ops)
        print("wrote", fname)
    est, diag = riders.estimate(con)
    riders_map(base, city, seg, lanes, est, diag, feeds, "m5_riders_v1_with_lanes.png")
    print("wrote m5_riders_v1_with_lanes.png", diag)
    lanes_map(base, city, lanes, "m6_bus_lane_sources.png")
    print("wrote m6_bus_lane_sources.png")


if __name__ == "__main__":
    main()
