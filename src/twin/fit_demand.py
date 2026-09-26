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
    candidate = resolve(cfg.get("candidate_routes", "sim/work/routes/candidates.rou.xml"))
    root = ET.parse(candidate).getroot()
    edges = {e.getID() for e in __import__("sumolib").net.readNet(str(resolve(cfg["network"]))).getEdges()}
    ordered = sorted(data["detectors"], key=lambda d: (d.get("position_m") is None, d.get("id", "")))
    # Mapping file supplies the map-matched edge IDs. Ordering is the user's corridor order, if provided.
    mapping_path = resolve(cfg.get("detector_additional", "sim/detectors.add.xml")).with_suffix(".csv")
    import csv
    edge_by_id = {}
    with open(mapping_path, encoding="utf-8") as f:
        for row in csv.DictReader(f): edge_by_id[row["detector_id"]] = row["edge_id"]
    target = defaultdict(float)
    calibration_coverage = {}
    calibration_seconds = float(cfg.get("calibration_seconds", 3600))
    interval_seconds = float(data.get("interval_seconds", 300))
    calibration_slots = max(1, int(round(calibration_seconds / interval_seconds)))
    for d in ordered:
        # Fit to the initial pre-incident calibration window only. The detector
        # export is a full, time-ordered grid, so later incident/recovery counts
        # must not inflate the baseline demand.
        observations = d.get("observations", [])[:calibration_slots]
        vals = [float(o["count"]) for o in observations if o.get("count") is not None]
        if vals:
            # Missing archive bins are not zero flow. Scale the observed total
            # to the declared calibration span, and retain the observed fraction
            # so a weakly sampled detector is visible in the fit report.
            observed_seconds = len(vals) * interval_seconds
            target[d["id"]] = sum(vals) * calibration_seconds / observed_seconds
            calibration_coverage[d["id"]] = len(vals) / max(len(observations), 1)
    routes = []
    for vehicle in root.findall("vehicle") + root.findall("flow"):
        route = vehicle.find("route")
        if route is None: continue
        rid, path = vehicle.get("id"), route.get("edges", "").split()
        if path and all(e in edges for e in path):
            crossings = {did for did, de in edge_by_id.items() if de in path}
            if crossings: routes.append((rid, path, crossings))
    if not routes or not target:
        raise ValueError("Need candidate routes, detector mappings, and non-null pre-incident observed counts.")
    # Coordinate descent on predicted detector totals, with nonnegative trip counts.
    # Keep predictions incremental: recomputing every detector's total for each
    # route update makes this quadratic in the number of random-trip candidates.
    flow = [1.0 for _ in routes]
    predicted = defaultdict(float)
    for value, (_, _, crosses) in zip(flow, routes):
        for did in crosses:
            predicted[did] += value
    for _ in range(args.iterations):
        for i, (_, _, crosses) in enumerate(routes):
            if not crosses:
                continue
            updated = max(0.0, sum(target[did] - predicted[did] + flow[i]
                                   for did in crosses) / len(crosses))
            change = updated - flow[i]
            if change:
                for did in crosses:
                    predicted[did] += change
                flow[i] = updated
    out = resolve(cfg.get("routes", "sim/work/routes/fitted.rou.xml")); out.parent.mkdir(parents=True, exist_ok=True)
    # Emit one rate-based flow per route across the full simulation horizon.
    fitted_root = ET.Element("routes")
    for typ in root.findall("vType"): fitted_root.append(typ)
    calibration_seconds = max(1, float(cfg.get("calibration_seconds", 3600)))
    simulation_begin = float(cfg.get("begin", 0))
    simulation_seconds = max(1.0, float(cfg.get("end", 7200)) - simulation_begin)
    scale = simulation_seconds / calibration_seconds
    vehicle_counts = [int(round(value * scale)) for value in flow]
    vehicle_total = sum(vehicle_counts)
    for serial, ((_, path, _), count) in enumerate(zip(routes, vehicle_counts)):
        if count <= 0:
            continue
        v = ET.SubElement(fitted_root, "flow", id=f"fit_{serial}", type="DEFAULT_VEHTYPE",
                          begin=f"{simulation_begin:.2f}", end=f"{simulation_begin + simulation_seconds:.2f}",
                          number=str(count), departLane="random", departSpeed="desired")
        ET.SubElement(v, "route", edges=" ".join(path))
    ET.ElementTree(fitted_root).write(out, encoding="utf-8", xml_declaration=True)
    predictions = dict(predicted)
    summary = {"target_counts": dict(target), "predicted_counts": predictions,
               "calibration_coverage_fraction": calibration_coverage,
               "calibration_window_slots": calibration_slots,
               "calibration_seconds": calibration_seconds,
               "simulation_seconds": simulation_seconds,
               "simulation_to_calibration_scale": scale,
               "candidate_routes_used": len(routes), "vehicles_generated": vehicle_total,
               "warning": "Simple linear route-weight estimate. Missing calibration bins are scaled using the observed-bin fraction; verify route direction/order and fit against a proper simulation before claiming calibration."}
    summary_path = out.with_name("fit-summary.json"); summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Fitted candidate route weights: {out}\nFit summary: {summary_path}")


if __name__ == "__main__": main()
