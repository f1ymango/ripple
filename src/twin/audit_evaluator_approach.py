"""Record the P0 fork and ramp connections without changing the network."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import sumolib

EDGES = ("814979901#0", "1198059118", "1198059119", "1198059120",
         "44419212", "1198101497", "1198101443", "46766432",
         "46766434#1", "485146396", "462275986#1", "1194711693")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("network", "osm", "out"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    net = sumolib.net.readNet(str(args.network))
    wanted = {edge.split("#")[0] for edge in EDGES}
    tags = {}
    for _, element in ET.iterparse(args.osm, events=("end",)):
        if element.tag == "way":
            if element.get("id") in wanted:
                tags[element.get("id")] = {t.get("k"): t.get("v") for t in element.findall("tag")}
            element.clear()
    rows = []
    for edge_id in EDGES:
        edge = net.getEdge(edge_id)
        rows.append({"edge_id": edge_id, "length_m": edge.getLength(),
                     "osm_tags": tags.get(edge_id.split("#")[0], {}),
                     "lanes": [{"lane_id": lane.getID(), "index": lane.getIndex(),
                                "passenger_allowed": lane.allows("passenger"),
                                "outgoing": [{"lane": c.getToLane().getID(), "state": c.getState()}
                                             for c in lane.getOutgoing()]}
                               for lane in edge.getLanes()]})
    xml = ET.parse(args.network).getroot()
    tls_ids = {c.get("tl") for c in xml.findall("connection") if c.get("from") == "46766432"}
    report = {"purpose": "Static evidence only; lane-change failure and real ramp priority remain unverified",
              "sources": {name: {"path": str(getattr(args, name)),
                                  "sha256": hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()}
                          for name in ("network", "osm")},
              "edges": rows,
              "late_warning_edge_length_m": sum(net.getEdge(e).getLength() for e in EDGES[2:4]),
              "earlier_warning_edge_length_m": sum(net.getEdge(e).getLength() for e in EDGES[:4]),
              "ramp_signal_programs": [{"id": t.get("id"), "phases": [p.attrib for p in t.findall("phase")]}
                                       for t in xml.findall("tlLogic") if t.get("id") in tls_ids]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
