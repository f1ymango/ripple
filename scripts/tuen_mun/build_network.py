"""Tuen Mun twin, step 1: the road network for IN-26-02615 (Tuen Mun Road, Tuen Mun bound, near Hong Kong Garden).

    python scripts/tuen_mun/build_network.py --irn /path/to/RdNet_IRNP.gdb
    -> sim/tuen-mun/speed-limits.edg.xml   TD's signed limits on each edge (committed; rebuilds need no gdb)
       sim/tuen-mun/network.net.xml        the network E runs
       sim/tuen-mun/network-audit.md       routes, lanes, limits and what was matched to TD's network
    The crash site is cut out of the long Tuen Mun Road edge by sim/tuen-mun/crash-site.edg.xml.

Geometry, lanes, turn lanes and traffic-light positions are OpenStreetMap's
(data/tuen-mun/osm/, an Overpass extract kept with its query and hash).
OpenStreetMap leaves most speed limits untagged and netconvert then guesses
from the road type (100 km/h on Castle Peak Road), so every edge takes TD's
signed limit from the Road Network's SPEED_LIMIT layer instead, matched by
position and direction; an edge with no signed limit nearby gets Hong Kong's
default of 50 km/h. Signal timings are netconvert's guesses: TD publishes none.
"""
import argparse
import gzip
import hashlib
import math
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OSM = ROOT / "data/tuen-mun/osm/tuen-mun.osm.xml.gz"
OUT = ROOT / "sim/tuen-mun"
BOUNDARY = "113.995,22.345,114.100,22.385"          # lon/lat: Siu Lam/So Kwun Wat to Yau Kom Tau
DEFAULT_KMH = 50                                      # Road Traffic Ordinance: 50 km/h unless signed otherwise
MATCH_M = 15                                          # an edge sample counts as on a limit section within this distance
# Castle Peak Road and the other non-motorway roads: free speed = limit x this. Fitted on the ordinary Wednesdays
# (22 Apr, 6 May) so the model's travel times match TD's segment speeds there (scripts/tuen_mun/segment_check.py):
# at the limits the model ran Castle Peak Rd at about 60 km/h where TD measures 42-44 km/h, signals included.
ARTERIAL_SPEED_FACTOR = 0.68
ARTERIAL_TYPES = ("highway.primary", "highway.secondary", "highway.tertiary", "highway.unclassified",
                  "highway.residential", "highway.living_street", "highway.primary_link", "highway.secondary_link",
                  "highway.tertiary_link")
NETCONVERT = ["netconvert", "--junctions.join", "true", "--tls.join", "true", "--roundabouts.guess", "true",
              "--lefthand", "--keep-edges.by-vclass", "passenger", "--geometry.remove", "true",
              "--output.street-names", "true", "--keep-edges.in-geo-boundary", BOUNDARY,
              "--remove-edges.by-type", "highway.service", "--osm.turn-lanes", "true",
              "--tls.default-type", "actuated"]          # TD publishes no timings: vehicle-actuated, checked against TD speeds
# the two ways from the Sham Tseng exit to Siu Lam, for the audit
MAIN_FROM, MAIN_TO = "645999370", "1078219416"
CLOSED_SPAN = {"389939170-scene"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_base(tmp):
    osm = Path(tmp) / "tuen-mun.osm.xml"
    osm.write_bytes(gzip.decompress(OSM.read_bytes()))
    base = Path(tmp) / "base.net.xml"
    subprocess.run(NETCONVERT + ["--osm-files", str(osm), "--output-file", str(base)], check=True,
                   stdout=subprocess.DEVNULL)
    return base


def td_limits(gdb, net):
    """Each passenger edge's speed limit in km/h from TD's SPEED_LIMIT layer, and how it was found."""
    import pyogrio
    import shapely
    from pyproj import Transformer
    from shapely.strtree import STRtree
    import pyogrio.raw
    meta, _, geometry, fields = pyogrio.raw.read(gdb, layer="SPEED_LIMIT")
    column = dict(zip(meta["fields"], fields))
    lines = [shapely.line_merge(g) if g.geom_type == "MultiLineString" else g for g in shapely.from_wkb(geometry)]
    lines = [g if g.geom_type == "LineString" else max(g.geoms, key=lambda x: x.length) for g in lines]
    kmh = [float(str(v).split()[0]) for v in column["SPEED_LIMIT"]]
    tree = STRtree(lines)
    to_grid = Transformer.from_crs(4326, 2326, always_xy=True)
    result = {}
    for edge in net.getEdges():
        if not edge.allows("passenger"):
            continue
        pts = [to_grid.transform(*net.convertXY2LonLat(x, y)) for x, y in edge.getShape()]
        line = shapely.LineString(pts)
        votes = Counter()
        for f in (0.2, 0.5, 0.8):
            p = line.interpolate(f, normalized=True)
            q = line.interpolate(min(1, f + 0.05), normalized=True), line.interpolate(max(0, f - 0.05), normalized=True)
            heading = math.atan2(q[0].y - q[1].y, q[0].x - q[1].x)
            best = None
            for i in tree.query(p.buffer(MATCH_M)):
                d = lines[i].distance(p)
                if d > MATCH_M:
                    continue
                s = lines[i].project(p)
                a, b = lines[i].interpolate(max(0, s - 5)), lines[i].interpolate(s + 5)
                if abs(math.cos(math.atan2(b.y - a.y, b.x - a.x) - heading)) < 0.85:
                    continue                                    # a crossing road, not this one
                if best is None or d < best[0]:
                    best = (d, kmh[i])
            if best:
                votes[best[1]] += 1
        result[edge.getID()] = (votes.most_common(1)[0][0], "TD signed limit") if votes else \
            (DEFAULT_KMH, "no signed limit within 15 m: default 50 km/h")
    return result


def write_patch(limits, path):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             "<!-- TD Road Network SPEED_LIMIT (RdNet_IRNP.gdb), matched to each OSM edge by position and "
             "direction; 50 km/h where no limit is signed. scripts/tuen_mun/build_network.py -->", "<edges>"]
    for edge_id, (kmh, how) in sorted(limits.items()):
        lines.append(f'    <edge id="{edge_id}" speed="{kmh / 3.6:.2f}"/>')
    lines.append("</edges>")
    path.write_text("\n".join(lines) + "\n")


def write_arterial_speeds(net, path):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f"<!-- Non-motorway roads run at {ARTERIAL_SPEED_FACTOR} x TD's limit: fitted to TD's ordinary-day segment "
             "speeds on Castle Peak Road (scripts/tuen_mun/build_network.py, ARTERIAL_SPEED_FACTOR) -->", "<edges>"]
    for edge in sorted(net.getEdges(), key=lambda e: e.getID()):
        if edge.getType() in ARTERIAL_TYPES and edge.allows("passenger"):
            lines.append(f'    <edge id="{edge.getID()}" speed="{edge.getSpeed() * ARTERIAL_SPEED_FACTOR:.2f}"/>')
    path.write_text("\n".join(lines + ["</edges>"]) + "\n")


def free_flow_path(net, start, goal, banned=frozenset()):
    import heapq
    import itertools
    tie, a, b = itertools.count(), net.getEdge(start), net.getEdge(goal)
    dist, prev, pq = {a: 0.0}, {}, [(0.0, next(tie), a)]
    while pq:
        d, _, e = heapq.heappop(pq)
        if e == b:
            break
        if d > dist[e]:
            continue
        for o in e.getOutgoing():
            if o.getID() in banned or not o.allows("passenger"):
                continue
            nd = d + o.getLength() / o.getSpeed()
            if nd < dist.get(o, math.inf):
                dist[o], prev[o] = nd, e
                heapq.heappush(pq, (nd, next(tie), o))
    path = [b]
    while path[-1] != a:
        path.append(prev[path[-1]])
    return path[::-1], dist[b]


def audit(net, limits, path):
    sources = Counter(how for _, how in limits.values())
    out = ["# Tuen Mun network audit", "",
           f"OpenStreetMap extract `{OSM.relative_to(ROOT)}` (sha256 of the gzip {sha256(OSM)[:12]}), "
           f"boundary {BOUNDARY}.", "",
           f"Passenger edges: {len(limits)}. Speed limits: "
           + ", ".join(f"{n} {how}" for how, n in sources.items()) + ".", "",
           f"Traffic lights: {len(net.getTrafficLights())}, all with netconvert's guessed programmes "
           "(TD publishes no timings).", ""]
    main, main_s = free_flow_path(net, MAIN_FROM, MAIN_TO)
    alt, alt_s = free_flow_path(net, MAIN_FROM, MAIN_TO, banned=CLOSED_SPAN)
    for title, p, s in (("Tuen Mun Road (Sham Tseng exit to Siu Lam)", main, main_s),
                        ("Castle Peak Road way round (same ends)", alt, alt_s)):
        signals = [e.getToNode().getID() for e in p if e.getToNode().getType() == "traffic_light"]
        out += [f"## {title}", "",
                f"{sum(e.getLength() for e in p[1:]) / 1000:.2f} km, {s / 60:.1f} min at free speed, "
                f"{len(signals)} traffic lights.", "",
                "| Edge | Road | Lanes | Length m | Free speed km/h | Limit from |", "|---|---|---|---|---|---|"]
        for e in p:
            out.append(f"| {e.getID()} | {(e.getName() or '').split(' ', 1)[-1]} | {e.getLaneNumber()} | "
                       f"{e.getLength():.0f} | {round(e.getSpeed() * 3.6)} | {limits[e.getID()][1]} |")
        out.append("")
    path.write_text("\n".join(out) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--irn", help="TD's RdNet_IRNP.gdb; without it the committed speed-limits.edg.xml is used")
    parser.add_argument("--crash-site", default="sim/tuen-mun/crash-site.edg.xml",
                        help="where the scene is cut out; a variant writes its own network and no audit")
    parser.add_argument("--output", default="sim/tuen-mun/network.net.xml")
    args = parser.parse_args()
    output, crash_site = ROOT / args.output, ROOT / args.crash_site
    variant = output != OUT / "network.net.xml"
    import sumolib
    OUT.mkdir(parents=True, exist_ok=True)
    patch = OUT / "speed-limits.edg.xml"
    with tempfile.TemporaryDirectory() as tmp:
        base = build_base(tmp)
        net = sumolib.net.readNet(str(base))
        if args.irn:
            write_patch(td_limits(args.irn, net), patch)
        limited = Path(tmp) / "limited.net.xml"
        subprocess.run(["netconvert", "--sumo-net-file", str(base), "--edge-files", str(patch), "--lefthand",
                        "--output-file", str(limited)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cut = Path(tmp) / "cut.net.xml"
        subprocess.run(["netconvert", "--sumo-net-file", str(limited), "--edge-files", str(crash_site),
                        "--lefthand", "--output-file", str(cut)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not variant:
            write_arterial_speeds(sumolib.net.readNet(str(cut)), OUT / "arterial-speeds.edg.xml")
        # corrections to OSM and the Sham Tseng Interchange stages: each file says why
        subprocess.run(["netconvert", "--sumo-net-file", str(cut),
                        "--edge-files", f"{OUT / 'fixes.edg.xml'},{OUT / 'arterial-speeds.edg.xml'}",
                        "--connection-files", str(OUT / "fixes.con.xml"), "--node-files", str(OUT / "fixes.nod.xml"),
                        "--tllogic-files", str(OUT / "signals.tll.xml"), "--lefthand",
                        "--output-file", str(output)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if variant:
        print("wrote", output, file=sys.stderr)
        return
    net = sumolib.net.readNet(str(OUT / "network.net.xml"))
    limits = {}
    for line in patch.read_text().splitlines():
        if line.strip().startswith("<edge "):
            edge_id = line.split('id="')[1].split('"')[0]
            limits[edge_id] = (float(line.split('speed="')[1].split('"')[0]) * 3.6, "")
    for edge in net.getEdges():
        if edge.getID().startswith("389939170-"):
            limits[edge.getID()] = limits["389939170"]
    if args.irn:
        limits = td_limits(args.irn, net)
    audit(net, limits, OUT / "network-audit.md")
    print("wrote", OUT / "network.net.xml", "and", OUT / "network-audit.md", file=sys.stderr)


if __name__ == "__main__":
    main()
