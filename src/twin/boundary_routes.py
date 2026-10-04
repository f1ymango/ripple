"""Experimental routes through existing entries/exits supported by Data's net flows.

No road, connection or volume is invented. Net flow differences identify eligible
stretches, not observed OD splits. Route weights must be inferred by fit_demand;
multiple approaches remain unidentifiable from these aggregate observations.
"""
import argparse
import json
import xml.etree.ElementTree as ET

import sumolib
from src.twin.common import load_json, resolve
from src.twin.network_sources import sha256
from src.twin.route_crossings import read_mapping


def neighbours(edge, incoming=False):
    """Only connections whose from/to lanes both admit passenger cars."""
    connections = edge.getIncoming() if incoming else edge.getOutgoing()
    return sorted((other for other, turns in connections.items()
                   if any(c.getFromLane().allows("passenger") and
                          c.getToLane().allows("passenger") for c in turns)),
                  key=lambda item: item.getID())


def external_branch(first, spine_ids, incoming, detector_edges):
    """Follow an unambiguous branch to its first junction; reject spine bypasses.

The edge count bounds this walk even on malformed cyclic networks. The returned
    list is always in driving order. Stop at another detector edge; the fitter
    must include that additional detector crossing, even on a different leg.
"""
    walk, seen = [], set()
    edge = first
    while edge.getID() not in seen:
        eid = edge.getID()
        if eid in spine_ids:
            return []
        walk.append(edge)
        seen.add(eid)
        if eid in detector_edges:
            break
        adjacent = neighbours(edge, incoming)
        if len(adjacent) != 1:
            break
        edge = adjacent[0]
    else:
        return []
    return list(reversed(walk)) if incoming else walk


def combine_paths(spine, entries, exits):
    """Use only connected paths along this directed corridor, without loops."""
    paths = set()
    for start, prefix in entries:
        for end, suffix in exits:
            if start > end:
                continue
            path = prefix + spine[start:end + 1] + suffix
            ids = tuple(edge.getID() for edge in path)
            if len(ids) != len(set(ids)):
                continue
            if all(b in neighbours(a) for a, b in zip(path, path[1:])):
                paths.add(ids)
    return sorted(paths)


def build_chain(net, chain, mapping):
    detector_edges = {item[0] for item in mapping.values()}
    ids = chain["detectors"]
    spine = [net.getEdge(mapping[ids[0]][0])]
    for did in ids[1:]:
        destination = net.getEdge(mapping[did][0])
        if destination == spine[-1]:
            continue
        path, _ = net.getShortestPath(spine[-1], destination, vClass="passenger")
        if not path:
            raise ValueError(f"No directed corridor path to {did}")
        spine.extend(path[1:])
    spine_ids = [edge.getID() for edge in spine]
    if len(spine_ids) != len(set(spine_ids)):
        raise ValueError("Corridor spine loops back; review placements")
    entries, exits, audit = [], [], []

    def add(index, incoming, evidence):
        connected = neighbours(spine[index], incoming)
        for edge in connected:
            if edge.getID() in spine_ids:
                continue
            branch = external_branch(edge, set(spine_ids), incoming, detector_edges)
            if not branch:
                continue
            target = entries if incoming else exits
            if (index, branch) not in target:
                target.append((index, branch))
                audit.append({"kind": "entry" if incoming else "exit",
                              "at_edge": spine_ids[index],
                              "branch": [e.getID() for e in branch], "evidence": evidence})

    add(0, True, {"type": "upstream corridor boundary", "detector": ids[0]})
    add(len(spine) - 1, False, {"type": "downstream corridor boundary", "detector": ids[-1]})
    if not entries or not exits:
        raise ValueError(f"Missing actual boundary for {ids[0]}..{ids[-1]}")
    unresolved = []
    for step in chain["steps"]:
        # Sampling evidence selects opportunities; it is never an invented
        # turning-volume constraint. Fit targets retain the frozen cov40 series.
        if abs(step["change_veh_h"]) <= step["margin_veh_h"]:
            continue
        left = spine_ids.index(mapping[step["from"]][0])
        right = spine_ids.index(mapping[step["to"]][0])
        incoming = step["change_veh_h"] > 0
        before = len(audit)
        indices = range(left + 1, right + 1) if incoming else range(left, right)
        for index in indices:
            add(index, incoming, {"type": "observed net change", **step})
        if len(audit) == before:
            unresolved.append(step)
    paths = combine_paths(spine, entries, exits)
    return paths, {"spine": spine_ids, "boundaries": audit,
                   "unresolved_net_changes": unresolved, "candidate_count": len(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--flow-evidence", required=True)
    parser.add_argument("--out", required=True, help="New experiment directory")
    args = parser.parse_args()
    cfg = load_json(resolve(args.config))
    evidence = load_json(resolve(args.flow_evidence))
    mapping_path = resolve(cfg["detector_additional"]).with_suffix(".csv")
    mapping = read_mapping(mapping_path)
    net = sumolib.net.readNet(str(resolve(cfg["network"])))
    all_paths, audits = set(), {}
    for name, chain in evidence["chains"].items():
        paths, audit = build_chain(net, chain, mapping)
        all_paths.update(paths)
        audits[name] = audit
    out = resolve(args.out)
    out.mkdir(parents=True, exist_ok=False)
    root = ET.Element("routes")
    for typ in ET.parse(resolve(cfg["routes"])).getroot().findall("vType"):
        root.append(typ)
    for index, path in enumerate(sorted(all_paths)):
        vehicle = ET.SubElement(root, "vehicle", id=f"boundary_{index}",
                                type="DEFAULT_VEHTYPE", depart="0", departPos="0")
        ET.SubElement(vehicle, "route", edges=" ".join(path))
    candidates = out / "candidates.rou.xml"
    ET.ElementTree(root).write(candidates, encoding="utf-8", xml_declaration=True)
    reference_routes = resolve(cfg["routes"])
    cfg["candidate_routes"] = candidates.relative_to(resolve(".")).as_posix()
    cfg["routes"] = (out / "fitted.rou.xml").relative_to(resolve(".")).as_posix()
    # This experiment fits/runs no closure. Retain the original end and rate
    # horizon so a shortened route file cannot alter departure rounding.
    (out / "scenario.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    sources = {"config": resolve(args.config), "flow_evidence": resolve(args.flow_evidence),
               "mapping": mapping_path, "network": resolve(cfg["network"]),
               "reference_routes": reference_routes}
    report = {"method": "Data-supported net-flow stretches, existing passenger connections only",
              "sources": {k: {"path": str(v), "sha256": sha256(v)} for k, v in sources.items()},
              "candidate_sha256": sha256(candidates), "chains": audits,
              "limitations": ["Aggregate counts do not identify unique OD or approach splits.",
                              "No source volume has been assigned to individual side roads.",
                              "Constant fitted rate is extrapolated through the 15-minute warm-up.",
                              "Provisional network and detector placements remain unchanged."]}
    (out / "boundary-audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(all_paths)} candidates to {out}")


if __name__ == "__main__":
    main()
