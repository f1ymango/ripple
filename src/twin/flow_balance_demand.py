"""SUMO demand and link speeds from Data's hand-over (src/loaders/twin_inputs.py).

A second way to build the twin's inputs, next to make_routes + fit_demand. It
uses the same rule as the backup network, so the two models are driven alike
and only the chains' first detectors set demand:

  demand   traffic enters upstream of each chain's first detector at that
           detector's own 15-minute counts. Between two neighbouring reporting
           detectors, the ordinary mornings' net change joins by the on-ramps
           the network has in that stretch, or leaves by its off-ramps (shared
           by lane count). Where the stretch has no such ramp, the change is
           applied on the main line and listed in the build report. Every
           vehicle is routed from where it comes in to an exit, or to the
           chain's end, with the exit shares applied in sequence.
  speeds   each chain edge moves at the ordinary mornings' quarter-hour speed
           of the detector it leads to, through a variable speed sign (a lane
           speed limit by time). An ordinary morning's slowdowns are then in
           the model without a queue having to be reproduced.

Three things in the network need care, and each is reported:
  * a short ramp or entry is extended upstream until vehicles have room to
    be inserted (RUN_IN_M);
  * where the road splits into two branches that rejoin, traffic is shared
    between them by lane count;
  * an entry road whose lanes lead only to an exit, with no room to change
    lane before it (WEAVE_M), carries exactly the traffic that leaves there.

    python -m src.twin.flow_balance_demand --inputs sim/scenarios/twin-inputs_20260515.json \\
        --network sim/work/aberdeen.flow-balance.net.xml --out sim/work/flow-balance
    -> demand.rou.xml, speeds.add.xml and build.json in --out
"""
import argparse
import datetime as dt
import json
import xml.etree.ElementTree as ET

from src.loaders.twin_inputs import CHAINS
from src.twin.common import load_json, resolve

MIN_POS_M = 30.0       # a detector this far into its edge reads that edge's speed
ENTRY_ON_EDGE_M = 100.0   # a first detector this far into its edge: traffic enters on that edge
RUN_IN_M = 100.0       # shorter ramps and entries are extended upstream
WEAVE_M = 100.0        # shorter edges give no room to change lane in dense traffic
SMALL = 0.05           # a change under 5% with no ramp to carry it is left out
VTYPE = {"speedFactor": "1", "speedDev": "0.05", "sigma": "0"}   # the speeds given already hold the drivers' spread
AUDIT = "results/twin/osm-network-audit.json"


def read_net(path):
    import sumolib
    return sumolib.net.readNet(str(resolve(path)), withInternal=True)


def _roads(edges, other):
    return [x for x in edges if x.getFunction() != "internal" and x.allows("passenger") and x.getID() != other]


def detectors_on(net, audit):
    """{detector: (edge id, position)} from the map audit, moved onto the second piece of an edge that was cut."""
    out = {}
    for d in audit["detectors"]:
        edge, pos = d["edge_id"], d["position_m"]
        for piece in split_pieces(net, edge):
            first = net.getEdge(edge).getLength()
            if pos > first:
                edge, pos = piece, pos - first
        out[d["detector_id"]] = (edge, pos)
    return out


def split_pieces(net, edge_id):
    """Edges cut off the end of `edge_id` by a netconvert split: named '<id>.<pos>', starting where it ends."""
    pieces, end = [], net.getEdge(edge_id).getToNode()
    while True:
        nxt = [x for x in end.getOutgoing() if x.getID().startswith(edge_id + ".")]
        if not nxt:
            return pieces
        pieces.append(nxt[0].getID())
        end = nxt[0].getToNode()


def chain_edges(net, audit, chain):
    """The chain's road, edge by edge, from its first detector's edge to its last's."""
    paths = {(p["from"], p["to"]): p["edges"] for p in audit["paths"]}
    edges = []
    for up, down in zip(chain, chain[1:]):
        for e in paths[(up, down)]:
            if not edges or edges[-1] != e:
                edges.append(e)
    out = []
    for e in edges:
        out += [e] + split_pieces(net, e)
    return out


def side_edges(net, es, i, kind):
    """Roads other than the chain's own that feed chain edge i ("in") or leave after it ("out")."""
    e = net.getEdge(es[i])
    if kind == "in":
        return [x for x in _roads(e.getFromNode().getIncoming(), es[i - 1] if i else None) if e in x.getOutgoing()]
    return [x for x in _roads(e.getToNode().getOutgoing(), es[i + 1] if i + 1 < len(es) else None)
            if x in e.getOutgoing()]


def bypasses(net, es):
    """{edge id: (i, j)}: single edges that leave after chain edge i and rejoin into chain edge j."""
    out = {}
    for i in range(len(es) - 1):
        for x in side_edges(net, es, i, "out"):
            for j in range(i + 2, len(es)):
                if net.getEdge(es[j]) in x.getOutgoing():
                    out[x.getID()] = (i, j)
    return out


def run_in(edge, min_m=RUN_IN_M):
    """[edge ids] ending with `edge`, extended upstream (the widest road each time) until `min_m` long."""
    path, length = [edge], edge.getLength()
    while length < min_m:
        ups = [x for x in _roads(path[0].getFromNode().getIncoming(), None)
               if path[0] in x.getOutgoing() and x not in path]
        if not ups:
            break
        path.insert(0, max(ups, key=lambda x: (x.getLaneNumber(), x.getLength())))
        length += path[0].getLength()
    return [x.getID() for x in path]


def exit_bound(net, es, feeder, exits):
    """The exit a feeder's lanes lead to with no lane on to the main line, or None.

    Follows the feeder's lanes edge by edge while the edges are too short to
    change lane on: if at an exit none of them connects to the next chain
    edge, its traffic can only take that exit.
    """
    lanes = {c.getToLane().getIndex() for c in feeder.getOutgoing()[net.getEdge(es[0])]}
    for i in range(len(es) - 1):
        e, nxt = net.getEdge(es[i]), net.getEdge(es[i + 1])
        on = {c.getToLane().getIndex() for c in e.getOutgoing().get(nxt, []) if c.getFromLane().getIndex() in lanes}
        here = [x for x in exits if x["after"] == i and x["edge"]]
        if here and not on:
            return here[0]
        if e.getLength() >= WEAVE_M or not on:
            return None
        lanes = on
    return None


def plan_chain(net, name, es, where, inputs, notes):
    """Where traffic comes in, where it leaves, and the chain's bypasses."""
    chain = [d for d in CHAINS[name] if d in where]
    idx = {d: es.index(where[d][0]) for d in chain}
    pos = {d: where[d][1] for d in chain}
    by = bypasses(net, es)

    def ramps(i, kind):
        return [x for x in side_edges(net, es, i, kind) if x.getID() not in by]

    origins, exits = [], []
    first = net.getEdge(es[0])
    if pos[chain[0]] >= ENTRY_ON_EDGE_M:
        origins.append({"kind": "entry", "start": 0, "prefix": [], "weight": 1.0})
    else:
        feeders = [x for x in _roads(first.getFromNode().getIncoming(), None) if first in x.getOutgoing()]
        lanes = sum(x.getLaneNumber() for x in feeders)
        origins += [{"kind": "entry", "start": 0, "prefix": run_in(x), "feeder": x.getID(),
                     "weight": x.getLaneNumber() / lanes} for x in feeders]
    for p in [p for p in inputs["pairs"] if p["chain"] == name]:
        iu, idn, label = idx[p["up"]], idx[p["down"]], f"{p['up']}->{p['down']}"
        same_edge = idn == iu
        between = (pos[p["up"]] + pos[p["down"]]) / 2 if same_edge else None
        if p["join_veh_h"] > 0:
            cand = [(i, x) for i in range(iu + 1, idn + 1) for x in ramps(i, "in")]
            lanes = sum(x.getLaneNumber() for _, x in cand)
            if cand:
                origins += [{"kind": "join", "start": i, "prefix": run_in(x), "pair": label,
                             "veh_h": p["join_veh_h"] * x.getLaneNumber() / lanes} for i, x in cand]
            elif p["join_veh_h"] / max(p["up_veh_h"], 1) < SMALL:
                notes.append(f"{label}: +{p['join_veh_h']:.0f} veh/h left out (no on-ramp between them, under {SMALL:.0%})")
            else:
                origins.append({"kind": "join on the main line", "start": iu if same_edge else iu + 1, "prefix": [],
                                "pair": label, "veh_h": p["join_veh_h"], "depart_pos": between})
                notes.append(f"{label}: +{p['join_veh_h']:.0f} veh/h joins on the main line "
                             "(the network has no on-ramp between them)")
        if p["exit_share"] > 0:
            cand = [(i, x) for i in range(iu, idn) for x in ramps(i, "out")]
            if cand:
                lanes, left = sum(x.getLaneNumber() for _, x in cand), 1.0
                for i, x in cand:            # in sequence, so that together they remove exit_share
                    part = p["exit_share"] * x.getLaneNumber() / lanes
                    exits.append({"after": i, "edge": x.getID(), "share": part / left, "pair": label})
                    left -= part
            elif p["exit_share"] < SMALL:
                notes.append(f"{label}: -{p['exit_share']:.1%} left out (no off-ramp between them, under {SMALL:.0%})")
            else:
                exits.append({"after": iu, "edge": None, "share": p["exit_share"], "pair": label,
                              "arrival_pos": between})
                notes.append(f"{label}: -{p['exit_share']:.1%} leaves on the main line "
                             "(the network has no off-ramp between them)")
    exits.sort(key=lambda x: x["after"])
    entries = [o for o in origins if o.get("feeder")]
    for o in entries:
        x = exit_bound(net, es, net.getEdge(o["feeder"]), exits)
        if x is None or len(entries) < 2:
            continue
        k, others = exits.index(x), [e for e in entries if e is not o]
        rest = sum(e["weight"] for e in others)
        o["weight"], o.setdefault("share_at", {})[k] = x["share"], 1.0
        for e in others:
            e["weight"] = e["weight"] / rest * (1 - x["share"])
            e.setdefault("share_at", {})[k] = 0.0
        notes.append(f"{name}: entry road {o['feeder']} leads only to exit {x['edge']}, so it carries the "
                     f"{x['share']:.1%} of the entry traffic that leaves there; the other entry road carries the rest")
    return origins, exits, by


def route_variants(net, es, by, first, last):
    """[(share, [edge ids])] from chain edge `first` to `last`, split at every bypass by lane count."""
    variants = [(1.0, list(range(first, last + 1)))]
    for bid, (bi, bj) in by.items():
        main = min(net.getEdge(es[k]).getLaneNumber() for k in range(bi + 1, bj))
        side = net.getEdge(bid).getLaneNumber()
        new = []
        for w, seq in variants:
            if bi in seq and bj in seq:
                a, b = seq.index(bi), seq.index(bj)
                new += [(w * main / (main + side), seq), (w * side / (main + side), seq[:a + 1] + [bid] + seq[b:])]
            else:
                new.append((w, seq))
        variants = new
    return [(w, [es[k] if isinstance(k, int) else k for k in seq]) for w, seq in variants]


def chain_flows(net, es, origins, exits, by, steps, step_s, offset_s, end_s):
    """[(begin, end, veh/h, edges, attributes)] for one chain."""
    flows = []
    for o in origins:
        stay, dests = 1.0, []
        for k, x in enumerate(exits):        # every exit at or after where it comes in, then the chain's end
            if x["after"] < o["start"]:
                continue
            if (x["edge"] is None and x.get("arrival_pos") is not None and x["after"] == o["start"]
                    and (o.get("depart_pos") or 0) > x["arrival_pos"]):
                continue
            share = o.get("share_at", {}).get(k, x["share"])
            dests.append((x, stay * share))
            stay *= 1 - share
        dests.append((None, stay))
        for x, frac in dests:
            if frac <= 0:
                continue
            last = len(es) - 1 if x is None else x["after"]
            for w, edges in route_variants(net, es, by, o["start"], last):
                edges = o["prefix"] + edges + ([x["edge"]] if x is not None and x["edge"] else [])
                attrs = {"departLane": "best", "departSpeed": "max"}
                if o.get("depart_pos"):
                    attrs["departPos"] = f"{o['depart_pos']:.1f}"
                if x is not None and x.get("arrival_pos") is not None:
                    attrs["arrivalPos"] = f"{x['arrival_pos']:.1f}"
                if o["kind"] == "entry":
                    for k, vph in enumerate(steps):
                        a, b = max(offset_s + k * step_s, 0.0), min(offset_s + (k + 1) * step_s, end_s)
                        if b > a:
                            flows.append((a, b, vph * o["weight"] * frac * w, edges, attrs))
                else:
                    flows.append((0.0, end_s, o["veh_h"] * frac * w, edges, attrs))
    return flows


def speed_detectors(net, es, where, chain, profiles, by):
    """{edge id: the detector whose speed it moves at}.

    The first detector well into the edge; else one at its very start (it reads
    the slower of this edge and the one before, so both carry its speed); else
    the next one downstream. The roads feeding the chain's first edge lead to
    its first detector.
    """
    placed = sorted((es.index(where[d][0]), where[d][1], d) for d in chain if d in where and d in profiles)
    out = {}
    for i, eid in enumerate(es):
        on = ([d for j, p, d in placed if j == i and p >= MIN_POS_M] or [d for j, p, d in placed if j == i])
        after = [d for j, p, d in placed if j > i]
        out[eid] = on[0] if on else after[0] if after else placed[-1][2]
    for bid, (_, bj) in by.items():
        out[bid] = out[es[bj]]
    first = net.getEdge(es[0])
    for x in _roads(first.getFromNode().getIncoming(), None):
        if first in x.getOutgoing():
            out.setdefault(x.getID(), placed[0][2])
    return out


def build(inputs, net, audit, begin, end_s, speeds=True):
    """(routes element, additional element, report) for a run starting at `begin` and lasting `end_s` seconds."""
    t0 = dt.datetime.fromisoformat(inputs["demand_steps_from"])
    offset = (t0 - begin).total_seconds()
    where = detectors_on(net, audit)
    notes, flows, plan, signs = [], [], {}, {}
    for name in CHAINS:
        es = chain_edges(net, audit, [d for d in CHAINS[name] if d in where])
        origins, exits, by = plan_chain(net, name, es, where, inputs, notes)
        plan[name] = {"edges": es, "origins": origins, "exits": exits, "bypasses": by}
        flows += chain_flows(net, es, origins, exits, by, inputs["entries"][name]["veh_h"],
                             inputs["demand_step_s"], offset, end_s)
        if speeds:
            signs.update(speed_detectors(net, es, where, CHAINS[name], inputs["speed_profile_kmh"], by))
    flows.sort(key=lambda f: f[0])           # SUMO reads flows in order of their begin
    routes = ET.Element("routes")
    ET.SubElement(routes, "vType", {"id": "DEFAULT_VEHTYPE", "vClass": "passenger", "length": "5", **VTYPE})
    expected = 0.0
    for i, (a, b, vph, edges, attrs) in enumerate(flows):
        vehicles = vph * (b - a) / 3600
        if vehicles < 0.05:
            continue
        expected += vehicles
        f = ET.SubElement(routes, "flow", {"id": f"f{i}", "type": "DEFAULT_VEHTYPE", "begin": f"{a:.0f}",
                                           "end": f"{b:.0f}", **attrs})
        if vehicles >= 8:
            f.set("number", str(round(vehicles)))
        else:                    # a small flow: random arrivals at its rate, so rounding adds no bias
            f.set("period", f"exp({vph / 3600:.6f})")
        ET.SubElement(f, "route", edges=" ".join(edges))
    additional = ET.Element("additional")
    minutes = inputs["speed_profile_minutes"]
    for eid, det in signs.items():
        e = net.getEdge(eid)
        lanes = [lane.getID() for lane in e.getLanes()]
        for nxt, conns in e.getOutgoing().items():    # and the junction lanes it leads into: traffic speeds
            if nxt.getID() in signs:                  # up or slows down on the next edge, not on the junction
                lanes += sorted({c.getViaLaneID() for c in conns if c.getViaLaneID()})
        sign = ET.SubElement(additional, "variableSpeedSign", id=f"vss_{eid}", lanes=" ".join(lanes))
        for key, kmh in sorted(inputs["speed_profile_kmh"][det].items()):
            t = (dt.datetime.combine(t0.date(), dt.time(int(key[:2]), int(key[3:])), t0.tzinfo) - begin).total_seconds()
            if t + minutes * 60 > 0 and t < end_s:
                ET.SubElement(sign, "step", time=f"{max(t, 0):.0f}", speed=f"{max(kmh, 5.0) / 3.6:.2f}")
    report = {"day": inputs["day"], "ordinary_days": inputs["ordinary_days"], "speeds": inputs["speeds"] if speeds else "none",
              "demand_setting_detectors": inputs["demand_setting_detectors"], "begin": begin.isoformat(),
              "end_seconds": end_s, "flows": len(routes.findall("flow")), "vehicles_expected": round(expected),
              "notes": notes, "speed_detector_by_edge": signs, "plan": plan}
    return routes, additional, report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inputs", required=True, help="Data's hand-over (python -m src.loaders.fetch twin-inputs)")
    ap.add_argument("--network", required=True)
    ap.add_argument("--audit", default=AUDIT, help="the map audit: detector positions and the paths between them")
    ap.add_argument("--out", required=True, help="directory for demand.rou.xml, speeds.add.xml and build.json")
    ap.add_argument("--begin", default="07:25", help="HH:MM the run starts (half an hour of warm-up before 07:55)")
    ap.add_argument("--end", default="08:55", help="HH:MM the run ends")
    ap.add_argument("--no-speeds", action="store_true", help="leave the network's own speed limits in place")
    args = ap.parse_args()
    inputs, audit = load_json(resolve(args.inputs)), load_json(resolve(args.audit))
    t0 = dt.datetime.fromisoformat(inputs["demand_steps_from"])
    begin, end = (dt.datetime.combine(t0.date(), dt.time.fromisoformat(x), t0.tzinfo) for x in (args.begin, args.end))
    routes, additional, report = build(inputs, read_net(args.network), audit, begin, (end - begin).total_seconds(),
                                       speeds=not args.no_speeds)
    out = resolve(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(routes).write(out / "demand.rou.xml", encoding="utf-8", xml_declaration=True)
    ET.ElementTree(additional).write(out / "speeds.add.xml", encoding="utf-8", xml_declaration=True)
    (out / "build.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{report['flows']} flows, about {report['vehicles_expected']} vehicles -> {out}")
    for line in report["notes"]:
        print("  " + line)


if __name__ == "__main__":
    main()
