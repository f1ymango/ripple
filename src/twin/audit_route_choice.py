"""Audit directed passenger paths for a proposed second incident detour.

This reads the existing SUMO network and scenario. It never adds connections,
vehicles, or roads. A graph path establishes only model connectivity; real
turn legality and demand still need independent source review.
"""
import argparse
import hashlib
import json
from collections import deque
from pathlib import Path
import xml.etree.ElementTree as ET

import sumolib


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def passenger_path(net, start, target, blocked):
    """Shortest edge-count path using existing passenger lane connections."""
    seen = {start: None}
    pending = deque([start])
    while pending:
        here = pending.popleft()
        if here == target:
            path = []
            while here is not None:
                path.append(here)
                here = seen[here]
            return list(reversed(path)), len(seen)
        for connections in net.getEdge(here).getOutgoing().values():
            for connection in connections:
                following = connection.getTo().getID()
                if (following not in seen and following not in blocked
                        and connection.getFromLane().allows("passenger")
                        and connection.getToLane().allows("passenger")):
                    seen[following] = here
                    pending.append(following)
    return None, len(seen)


def audit(network, scenario_path, osm=None):
    net = sumolib.net.readNet(str(network))
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    closure = scenario["closure"]
    closed = set(closure["detour"]["replace"])
    surface = closure["detour"]["with"]
    protected = set(scenario["metrics"]["emergency_route_edges"])
    protected |= {edge.getID() for edge in net.getEdges() if any(
        name in (edge.getName() or "").lower()
        for name in ("pok fu lam", "shek pai wan"))}
    origin = scenario["metrics"]["corridor"]["from_edge"]
    cases = {
        "closure_only": closed,
        "closure_and_hospital_corridor": closed | protected,
        "closure_and_surface_entry": closed | {surface[0]},
        "closure_hospital_and_surface_entry": closed | protected | {surface[0]},
    }
    cases.update({f"closure_hospital_and_surface_segment_{i}": closed | protected | {edge}
                  for i, edge in enumerate(surface[1:], start=1)})
    groups = {}
    for name, od in scenario["plan_actions"]["od_groups"].items():
        group = {}
        for case, blocked in cases.items():
            path, reachable = passenger_path(net, origin, od["to_edge"], blocked)
            group[case] = {"path_edges": path, "reachable_edges": reachable,
                           "path_road_names": [net.getEdge(e).getName() for e in path] if path else None,
                           "path_length_m": round(sum(net.getEdge(e).getLength() for e in path), 1) if path else None}
        groups[name] = {"destination_edge": od["to_edge"], "cases": group}
    alt = groups[next(iter(groups))]["cases"]["closure_hospital_and_surface_segment_7"]["path_edges"]
    usual = groups[next(iter(groups))]["cases"]["closure_and_hospital_corridor"]["path_edges"]
    branch = [edge for edge in alt if edge not in set(usual)] if alt else []
    tags = {}
    if osm:
        wanted = {edge.split("#")[0] for edge in branch}
        for _, element in ET.iterparse(osm, events=("end",)):
            if element.tag == "way" and element.get("id") in wanted:
                tags[element.get("id")] = {row.get("k"): row.get("v") for row in element.findall("tag")}
            if element.tag in ("way", "node"):
                element.clear()
    return {
        "purpose": "Gate 1 graph feasibility only; physical turn legality and route demand are not established",
        "sources": {"network": {"path": str(network), "sha256": digest(network)},
                    "scenario": {"path": str(scenario_path), "sha256": digest(scenario_path)},
                    **({"osm": {"path": str(osm), "sha256": digest(osm)}} if osm else {})},
        "origin_edge": origin,
        "closure_edges_blocked": sorted(closed),
        "existing_surface_detour_edges": surface,
        "surface_entry_blocked_for_second_route": surface[0],
        "protected_edge_count": len(protected),
        "late_branch_edges_only": [{"edge": edge, "road": net.getEdge(edge).getName(),
                                    "osm_tags": tags.get(edge.split("#")[0])} for edge in branch],
        "od_groups": groups,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--network", type=Path, required=True)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--osm", type=Path, help="Original OSM export for road tags; still needs physical review")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.network, args.scenario, args.osm)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    for name, group in result["od_groups"].items():
        print(name)
        for case, row in group["cases"].items():
            print(f"  {case}: {len(row['path_edges']) if row['path_edges'] else 0} path edges; "
                  f"{row['reachable_edges']} reachable edges")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
