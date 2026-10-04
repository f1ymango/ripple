import argparse
import json
import xml.etree.ElementTree as ET
from collections import defaultdict

from src.twin.common import load_json, resolve
from src.twin.route_crossings import read_mapping, crosses_detector


def main():
    ap = argparse.ArgumentParser(description="Estimate route weights from detector count totals with coordinate descent.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--detectors", required=True)
    ap.add_argument("--iterations", type=int, default=300)
    ap.add_argument("--no-closure", action="store_true",
                    help="Fit a no-closure diagnostic without suspending incident-edge origins")
    args = ap.parse_args()
    cfg, data = load_json(resolve(args.config)), load_json(resolve(args.detectors))
    if args.iterations < 1:
        raise ValueError("--iterations must be positive")
    candidate = resolve(cfg.get("candidate_routes", "sim/work/routes/candidates.rou.xml"))
    root = ET.parse(candidate).getroot()
    network_edges = __import__("sumolib").net.readNet(str(resolve(cfg["network"]))).getEdges()
    edges = {e.getID() for e in network_edges}
    lengths = {e.getID(): e.getLength() for e in network_edges if hasattr(e, "getLength")}
    ordered = sorted(data["detectors"], key=lambda d: (d.get("position_m") is None, d.get("id", "")))
    # Mapping file supplies the map-matched edge IDs. Ordering is the user's corridor order, if provided.
    mapping_path = resolve(cfg.get("detector_additional", "sim/detectors.add.xml")).with_suffix(".csv")
    mapping = read_mapping(mapping_path)
    edge_by_id = {did: item[0] for did, item in mapping.items()}
    target = {}
    calibration_coverage = {}
    calibration_seconds = float(cfg.get("calibration_seconds", 3600))
    if calibration_seconds <= 0:
        raise ValueError("calibration_seconds must be positive")
    interval_seconds = float(data.get("interval_seconds", 300))
    if interval_seconds <= 0:
        raise ValueError("Detector interval_seconds must be positive")
    slot_count = calibration_seconds / interval_seconds
    if not slot_count.is_integer():
        raise ValueError("calibration_seconds must be an exact multiple of detector interval_seconds")
    incident = cfg.get("incident", {})
    if incident.get("start") is not None:
        observed_start = float(cfg.get("observation_start_sim_seconds", cfg.get("warmup_seconds", 0)))
        available_preincident = float(incident["start"]) - observed_start
        if available_preincident < 0 or calibration_seconds > available_preincident:
            raise ValueError(
                "Demand calibration window overlaps the configured incident: "
                f"{calibration_seconds:g}s requested, {max(0, available_preincident):g}s available "
                "before incident.start. Set calibration_seconds to a pre-incident duration."
            )
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
    route_endpoints = []
    types = {item.get("id"): item for item in root.findall("vType")}
    for vehicle in root.findall("vehicle") + root.findall("flow"):
        route = vehicle.find("route")
        if route is None: continue
        rid, path = vehicle.get("id"), route.get("edges", "").split()
        if path and all(e in edges for e in path):
            # A detector with no usable calibration counts supplies no target.
            # Treating its missing value as zero suppresses flow on shared edges.
            depart, arrival = vehicle.get("departPos", "0"), vehicle.get("arrivalPos", "max")
            typ = types.get(vehicle.get("type", "DEFAULT_VEHTYPE"))
            length = float(typ.get("length", "5")) if typ is not None else 5.0
            crossings = {did for did, (de, pos) in mapping.items() if did in target
                         and crosses_detector(path, de, pos, lengths, depart, arrival, length)}
            if crossings:
                routes.append((rid, path, crossings))
                route_endpoints.append((depart, arrival, vehicle.get("type", "DEFAULT_VEHTYPE")))
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
    simulation_end = simulation_begin + simulation_seconds
    scale = simulation_seconds / calibration_seconds
    incident_edge = incident.get("edge_id")
    incident_start = float(incident.get("start", simulation_end))
    incident_end = incident_start + float(incident.get("duration_seconds", 0))
    incident_overlap = max(simulation_begin, incident_start) < min(simulation_end, incident_end)
    vehicle_total = 0
    unsuspended_vehicle_total = 0
    flow_serial = 0
    suspended_origin_routes = 0
    for route_serial, ((_, path, _), route_rate) in enumerate(zip(routes, flow)):
        count = int(round(route_rate * scale))
        if count <= 0:
            continue
        unsuspended_vehicle_total += count
        # Candidate trips start at detector edges, which are synthetic entry
        # points rather than real access roads. Do not inject new vehicles at
        # the blocked incident edge during the closure; upstream routes still
        # travel into the incident and form the queue. Resume the fitted rate
        # after reopening so the demand horizon remains consistent.
        if not args.no_closure and incident_edge and incident_edge not in {"REVIEW_REQUIRED", ""} \
                and path[0] == incident_edge and incident_overlap:
            suspended_origin_routes += 1
            segments = [
                (simulation_begin, min(simulation_end, incident_start),
                 route_rate * max(0, min(simulation_end, incident_start) - simulation_begin)
                 / calibration_seconds),
                (max(simulation_begin, incident_end), simulation_end,
                 route_rate * max(0, simulation_end - max(simulation_begin, incident_end))
                 / calibration_seconds),
            ]
        else:
            segments = [(simulation_begin, simulation_end, count)]
        for segment_no, (segment_begin, segment_end, segment_count) in enumerate(segments):
            segment_count = (int(round(segment_count)) if not isinstance(segment_count, int)
                             else segment_count)
            if segment_count <= 0 or segment_end <= segment_begin:
                continue
            flow_id = f"fit_{route_serial}"
            if len(segments) == 2:
                flow_id += "_pre" if segment_no == 0 else "_post"
            depart, arrival, vehicle_type = route_endpoints[route_serial]
            vehicle = ET.SubElement(
                fitted_root, "flow", id=flow_id, type=vehicle_type,
                begin=f"{segment_begin:.2f}", end=f"{segment_end:.2f}",
                number=str(segment_count), departLane="best", departPos=depart, arrivalPos=arrival,
                departSpeed="desired")
            ET.SubElement(vehicle, "route", edges=" ".join(path))
            vehicle_total += segment_count
            flow_serial += 1
    # SUMO loads routes incrementally. A late reopening flow before another
    # route's early flow makes SUMO ignore that early flow as unsorted.
    # Stable sorting retains route order for equal departure times.
    fitted_root[:] = (fitted_root.findall("vType") + sorted(
        fitted_root.findall("flow"), key=lambda item: float(item.get("begin"))))
    ET.ElementTree(fitted_root).write(out, encoding="utf-8", xml_declaration=True)
    predictions = dict(predicted)
    summary = {"target_counts": dict(target), "predicted_counts": predictions,
               "no_closure_fit": args.no_closure,
               "detectors_without_position": sorted(did for did, (_, pos) in mapping.items() if pos is None),
               "route_weights": [{"candidate": rid, "edges": path, "crossings": sorted(crosses),
                                   "calibration_count": value}
                                  for (rid, path, crosses), value in zip(routes, flow)],
               "detectors_without_calibration_counts": sorted(set(edge_by_id) - set(target)),
               "calibration_coverage_fraction": calibration_coverage,
               "calibration_window_slots": calibration_slots,
               "calibration_seconds": calibration_seconds,
               "simulation_seconds": simulation_seconds,
               "simulation_to_calibration_scale": scale,
               "candidate_routes_used": len(routes), "flows_generated": flow_serial,
               "routes_originating_on_incident_edge_suspended": suspended_origin_routes,
               "vehicles_generated": vehicle_total,
               "vehicles_before_origin_suspension": unsuspended_vehicle_total,
               "vehicles_removed_by_origin_suspension_including_rounding": unsuspended_vehicle_total - vehicle_total,
               "origin_suspension_is_modelling_assumption": bool(suspended_origin_routes),
               "warning": "Simple linear route-weight estimate. Missing calibration bins are scaled using the observed-bin fraction; verify route direction/order and fit against a proper simulation before claiming calibration."}
    summary_path = out.with_name("fit-summary.json"); summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Fitted candidate route weights: {out}\nFit summary: {summary_path}")


if __name__ == "__main__": main()
