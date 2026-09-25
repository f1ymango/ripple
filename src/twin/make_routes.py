import argparse
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict

import sumolib
from src.twin.common import load_json, resolve


def main():
    ap = argparse.ArgumentParser(description="Build detector-to-detector corridor routes from the matched map.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--detectors", default="sim/scenarios/detectors.json")
    args = ap.parse_args()
    cfg, data = load_json(resolve(args.config)), load_json(resolve(args.detectors))
    mapping = resolve(cfg.get("detector_additional", "sim/work/detectors.add.xml")).with_suffix(".csv")
    edge_by_id = {}
    with mapping.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            edge_by_id.setdefault(row["detector_id"], row["edge_id"])
    net = sumolib.net.readNet(str(resolve(cfg["network"])))
    groups = defaultdict(list)
    for d in data["detectors"]:
        edge_id = edge_by_id.get(d["id"])
        if edge_id and d.get("leg"):
            groups[d["leg"]].append((d["id"], net.getEdge(edge_id)))
    root = ET.Element("routes")
    ET.SubElement(root, "vType", id="DEFAULT_VEHTYPE", vClass="passenger", length="5", maxSpeed="16.7")
    route_no = 0
    for leg, sensors in sorted(groups.items()):
        for i, (_, source) in enumerate(sensors):
            for _, destination in sensors[i + 1:]:
                if source == destination:
                    continue
                path, _ = net.getShortestPath(source, destination, vClass="passenger")
                if not path or len(path) < 2:
                    continue
                v = ET.SubElement(root, "vehicle", id=f"{leg}_{route_no}", type="DEFAULT_VEHTYPE", depart="0")
                ET.SubElement(v, "route", edges=" ".join(edge.getID() for edge in path))
                route_no += 1
    if route_no == 0:
        raise ValueError("No directed detector-to-detector corridor paths; review map matching and detector leg fields.")
    out = resolve(cfg.get("candidate_routes", "sim/work/routes/candidates.rou.xml"))
    out.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {route_no} corridor routes to {out}")


if __name__ == "__main__":
    main()
