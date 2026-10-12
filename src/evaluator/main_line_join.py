"""Copy a demand file so that named flows join on the main line instead of by their on-ramp.

    python -m src.evaluator.main_line_join --routes sim/work/p0-replay-build/demand.rou.xml \\
        --flow f22 --from-edge 1194711693 --out sim/work/p0-replay-build/demand-main-line-join.rou.xml

For the replay: src/twin/flow_balance_demand.py puts the ordinary mornings'
join between AID01108 and AID01109, 783.5 veh/h, on the one on-ramp the network
has there (46766432). SUMO's merge at the end of that ramp lets far fewer in:
vehicles wait up to 27 minutes to enter from 07:45, before the crash, and
AID01109 counts 19% fewer than the detector did before the crash. The detector
shows the real ramp's traffic did get in. With --flow and --from-edge each
named flow's route starts at that main-line edge instead, so the same vehicles
join where the ramp meets the main line, at the same times.

Everything else in the file is copied unchanged. The output is a new
simulation input: it is hashed like any other and never overwritten.
"""
import argparse
import xml.etree.ElementTree as ET

from src.twin.common import resolve


def join_on_main_line(root, flow_ids, from_edge):
    """Start each named flow's route at `from_edge`. Returns {flow id: edges dropped}."""
    dropped = {}
    for flow in root.iter("flow"):
        if flow.get("id") not in flow_ids:
            continue
        route = flow.find("route")
        edges = route.get("edges").split()
        if from_edge not in edges:
            raise ValueError(f"Flow {flow.get('id')} does not pass {from_edge}")
        at = edges.index(from_edge)
        dropped[flow.get("id")] = edges[:at]
        route.set("edges", " ".join(edges[at:]))
    missing = set(flow_ids) - set(dropped)
    if missing:
        raise ValueError(f"No flow named {sorted(missing)} in the demand file")
    return dropped


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--routes", required=True)
    parser.add_argument("--flow", nargs="+", required=True, metavar="FLOW_ID")
    parser.add_argument("--from-edge", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = resolve(args.out)
    if out.exists():
        raise ValueError(f"{out} exists; a demand file is a hashed simulation input and is never overwritten")
    tree = ET.parse(resolve(args.routes))
    dropped = join_on_main_line(tree.getroot(), set(args.flow), args.from_edge)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    for flow, edges in sorted(dropped.items()):
        print(f"{flow}: starts at {args.from_edge}, no longer on {' '.join(edges)}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
