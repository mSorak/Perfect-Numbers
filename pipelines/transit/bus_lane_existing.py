"""Existing bus lanes in Baltimore as tagged in OpenStreetMap (Overpass snapshot)."""

import json

import pandas as pd
import shapely


def build(con, ctx):
    raw = ctx.raw("osm_overpass/baltimore_bus_lanes") / "overpass.json"
    snap = ctx.raw_inputs["osm_overpass/baltimore_bus_lanes"]["snapshot_id"]
    rows = []
    for el in json.loads(raw.read_text(encoding="utf-8"))["elements"]:
        if el.get("type") != "way" or not el.get("geometry"):
            continue
        t = el.get("tags", {})
        side = ("both" if "busway:both" in t else "right" if "busway:right" in t else
                "left" if "busway:left" in t else ("lane tags" if any(k.startswith(("lanes:bus", "bus:lanes")) for k in t)
                                                   else ("busway" if t.get("highway") == "busway" else None)))
        rows.append({
            "osm_way_id": el["id"], "street_name": t.get("name"), "highway": t.get("highway"),
            "bus_lane_side": side,
            "busway_tag": t.get("busway:right") or t.get("busway:left") or t.get("busway:both") or t.get("busway"),
            "lanes_bus": t.get("lanes:bus") or t.get("bus:lanes"),
            "colour": t.get("busway:colour"), "start_date": t.get("busway:start_date"),
            "oneway": t.get("oneway"),
            "geometry_wkt": shapely.LineString([(p["lon"], p["lat"]) for p in el["geometry"]]).wkt,
            "source_snapshot_id": snap,
        })
    df = pd.DataFrame(rows)
    con.register("_lanes", df)
    return "SELECT * EXCLUDE (geometry_wkt), ST_GeomFromText(geometry_wkt)::GEOMETRY('OGC:CRS84') AS geometry FROM _lanes"
