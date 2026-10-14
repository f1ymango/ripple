"""Tuen Mun twin check: modelled travel time along a route against TD's segment speeds for the same stretch.

    python scripts/tuen_mun/segment_check.py --day 2026-04-22 --edges sim/work/tuen-mun/ord-0422-a/edges.xml \\
        --irn /path/to/RdNet_IRNP.gdb [--route castle_peak_road ...]
    -> a table per route: minutes on the stretches TD measures, TD vs the model, every 15 minutes

TD's segment speeds (irnAvgSpeed, data/raw/segments) are per Road Network route id. Each model edge
is matched to the TD centreline it lies on (position and direction, as the speed limits are); the
comparison uses only the edges whose TD route id has a speed in that snapshot, on both sides.
"""
import argparse
import datetime as dt
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.loaders import archive   # noqa: E402

HK = dt.timezone(dt.timedelta(hours=8))
SEG = re.compile(rb"<segment_id>(\d+)</segment_id><speed>([\d.]+)</speed><valid>(\w)</valid>")
BEGIN = "16:30"
MATCH_M = 15


def centreline_ids(gdb, net, edge_ids):
    import pyogrio.raw
    import shapely
    from pyproj import Transformer
    from shapely.strtree import STRtree
    meta, _, geometry, fields = pyogrio.raw.read(gdb, layer="CENTERLINE")
    col = dict(zip(meta["fields"], fields))
    lines = [shapely.line_merge(g) if g.geom_type == "MultiLineString" else g for g in shapely.from_wkb(geometry)]
    lines = [g if g.geom_type == "LineString" else max(g.geoms, key=lambda x: x.length) for g in lines]
    rid = [int(v) for v in col["ROUTE_ID"]]
    tree, T = STRtree(lines), Transformer.from_crs(4326, 2326, always_xy=True)
    out = {}
    for edge_id in edge_ids:
        edge = net.getEdge(edge_id)
        line = shapely.LineString([T.transform(*net.convertXY2LonLat(x, y)) for x, y in edge.getShape()])
        p = line.interpolate(0.5, normalized=True)
        a, b = line.interpolate(0.45, normalized=True), line.interpolate(0.55, normalized=True)
        heading = math.atan2(b.y - a.y, b.x - a.x)
        best = None
        for i in tree.query(p.buffer(MATCH_M)):
            d = lines[i].distance(p)
            s = lines[i].project(p)
            u, v = lines[i].interpolate(max(0, s - 5)), lines[i].interpolate(s + 5)
            if d <= MATCH_M and abs(math.cos(math.atan2(v.y - u.y, v.x - u.x) - heading)) > 0.85 \
                    and (best is None or d < best[0]):
                best = (d, rid[i])
        out[edge_id] = best[1] if best else None
    return out


def td_speeds(day, minute):
    """Segment speeds in the archived snapshot nearest this clock minute: {route id: km/h}."""
    stamps = archive.list_versions("segments", day, day)
    target = dt.datetime.fromisoformat(f"{day}T{minute}")
    stamp = min(stamps, key=lambda s: abs((dt.datetime.strptime(s, "%Y%m%d-%H%M") - target).total_seconds()))
    return {int(s): float(v) for s, v, ok in SEG.findall(archive.fetch("segments", stamp)) if ok == b"Y"}


def model_speeds(edges_xml):
    """{(interval begin second, edge): m/s} from SUMO edgeData."""
    out = {}
    for interval in ET.parse(edges_xml).getroot().iter("interval"):
        begin = round(float(interval.get("begin")))
        for e in interval.iter("edge"):
            if e.get("speed") is not None and float(e.get("sampledSeconds", 0)) > 0:
                out[(begin, e.get("id"))] = float(e.get("speed"))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--day", required=True)
    parser.add_argument("--edges", required=True)
    parser.add_argument("--irn", required=True)
    parser.add_argument("--from", dest="start", default="17:00")
    parser.add_argument("--until", default="20:00")
    parser.add_argument("--route", nargs="*", default=None)
    args = parser.parse_args()
    import sumolib
    net = sumolib.net.readNet(str(ROOT / "sim/tuen-mun/network.net.xml"))
    routes = json.loads((ROOT / "sim/tuen-mun/demand_20260415.json").read_text())["routes"]
    scenario = json.loads((ROOT / "sim/scenarios/tuen-mun/evaluator_IN-26-02615_replay-v1.json").read_text())
    routes["plan:castle_peak_road"] = " ".join(scenario["plan_actions"]["routes"]["Castle Peak Road"]["with"])
    names = args.route or ["plan:castle_peak_road", "cpr_to_so_kwun_wat", "cpr_eastbound_to_tsuen_wan", "tmr_to_tuen_mun"]
    ids = centreline_ids(args.irn, net, sorted({e for n in names for e in routes[n].split()}))
    model = model_speeds(ROOT / args.edges)
    t0 = dt.datetime.fromisoformat(f"{args.day}T{BEGIN}")
    t, end = dt.datetime.fromisoformat(f"{args.day}T{args.start}"), dt.datetime.fromisoformat(f"{args.day}T{args.until}")
    print(f"{args.day}: minutes on the stretches TD measures (TD | model)")
    print("time   " + " ".join(n[:24].rjust(26) for n in names))
    while t < end:
        td = td_speeds(args.day, t.strftime("%H:%M"))
        second = int((t - t0).total_seconds()) // 300 * 300
        cells = []
        for n in names:
            a = b = length = 0.0
            for edge_id in routes[n].split():
                rid, L = ids.get(edge_id), net.getEdge(edge_id).getLength()
                m = model.get((second, edge_id)) or model.get((second + 300, edge_id))
                if rid in td and m:
                    a += L / (td[rid] / 3.6); b += L / m; length += L
            cells.append(f"{a / 60:5.1f} | {b / 60:5.1f} ({length / 1000:4.1f}km)".rjust(26))
        print(t.strftime("%H:%M"), " ".join(cells))
        t += dt.timedelta(minutes=15)


if __name__ == "__main__":
    main()
