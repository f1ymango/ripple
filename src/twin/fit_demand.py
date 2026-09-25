import argparse
import json
import xml.etree.ElementTree as ET
from collections import defaultdict

from src.twin.common import load_json, resolve


def main():
    ap = argparse.ArgumentParser(description="Estimate route weights from detector count totals with coordinate descent.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--detectors", required=True)
    ap.add_argument("--iterations", type=int, default=300)
    args = ap.parse_args()
    cfg, data = load_json(resolve(args.config)), load_json(resolve(args.detectors))
    candidate = resolve("sim/work/routes/candidates.rou.xml")
    root = ET.parse(candidate).getroot()
    edges = {e.getID() for e in __import__("sumolib").net.readNet(str(resolve(cfg["network"]))).getEdges()}
    ordered = sorted(data["detectors"], key=lambda d: (d.get("position_m") is None, d.get("id", "")))
    # Mapping file supplies the map-matched edge IDs. Ordering is the user's corridor order, if provided.
    mapping_path = resolve(cfg.get("detector_additional", "sim/work/network/real_detectors.add.xml")).with_suffix(".csv")
    import csv
    edge_by_id = {}
    with open(mapping_path, encoding="utf-8") as f:
        for row in csv.DictReader(f): edge_by_id[row["detector_id"]] = row["edge_id"]
    target = defaultdict(float)
    for d in ordered:
        vals = [o["count"] for o in d.get("observations", []) if o.get("count") is not None]
        if vals: target[d["id"]] = sum(vals)
    routes = []
    for vehicle in root.findall("vehicle"):
        route = vehicle.find("route")
        if route is None: continue
        rid, path = vehicle.get("id"), route.get("edges", "").split()
        if path and all(e in edges for e in path):
            crossings = {did for did, de in edge_by_id.items() if de in path}
            if crossings: routes.append((rid, path, crossings))
    if not routes or not target:
        raise ValueError("Need candidate routes, detector mappings, and non-null pre-incident observed counts.")
    # Coordinate descent on predicted detector totals, with nonnegative trip counts.
    flow = [1.0 for _ in routes]
    for _ in range(args.iterations):
        for i, (_, _, crosses) in enumerate(routes):
            numerator = denominator = 0.0
            for did, observed in target.items():
                a = 1.0 if did in crosses else 0.0
                pred = sum(flow[j] for j, (_, _, c) in enumerate(routes) if did in c)
                numerator += a * (observed - pred + a * flow[i])
                denominator += a * a
            if denominator: flow[i] = max(0.0, numerator / denominator)
    out = resolve(cfg.get("routes", "sim/work/routes/fitted.rou.xml")); out.parent.mkdir(parents=True, exist_ok=True)
    # Convert fitted route-level trips to explicit vehicles spread over the observed hour.
    fitted_root = ET.Element("routes")
    for typ in root.findall("vType"): fitted_root.append(typ)
    span = max(1, int(cfg.get("calibration_seconds", 3600)))
    serial = 0
    for (rid, path, _), value in zip(routes, flow):
        for k in range(int(round(value))):
            v = ET.SubElement(fitted_root, "vehicle", id=f"fit_{serial}", type="DEFAULT_VEHTYPE", depart=f"{(serial * span / max(1, round(sum(flow)))):.2f}")
            ET.SubElement(v, "route", edges=" ".join(path))
            serial += 1
    fitted_root.write(out, encoding="utf-8", xml_declaration=True)
    predictions = {did: sum(v for (_, _, c), v in zip(routes, flow) if did in c) for did in target}
    summary = {"target_counts": dict(target), "predicted_counts": predictions,
               "warning": "Simple linear route-weight estimate. Verify route direction/order and fit against a proper simulation before claiming calibration."}
    summary_path = out.with_name("fit-summary.json"); summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Fitted candidate route weights: {out}\nFit summary: {summary_path}")


if __name__ == "__main__": main()
