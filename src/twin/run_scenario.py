import argparse
import os
import sys
from pathlib import Path

from src.twin.common import load_json, require_command, resolve, sumo_tools


def main():
    ap = argparse.ArgumentParser(description="Run baseline/plan with an incident lane closure controlled by TraCI.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--label", default="baseline")
    ap.add_argument("--plan-routes")
    ap.add_argument("--compliance", type=float, default=0.0)
    ap.add_argument("--clearance", type=float, default=60.0)
    args = ap.parse_args()
    cfg = load_json(resolve(args.config))
    import traci
    from src.twin import policies
    net, routes = resolve(cfg["network"]), resolve(args.plan_routes or cfg["routes"])
    add = resolve(cfg["detector_additional"])
    output = resolve(cfg.get("output_dir", "sim/work/results")); output.mkdir(parents=True, exist_ok=True)
    cmd = [require_command("sumo"), "-n", str(net), "-r", str(routes), "-a", str(add),
           "--begin", str(cfg.get("begin", 0)), "--end", str(cfg.get("end", 7200)),
           "--step-length", str(cfg.get("step_length", 1)), "--seed", str(cfg.get("seed", 2026)),
           "--no-step-log", "true"]
    traci.start(cmd, label=args.label)
    incident = cfg["incident"]; start, duration = float(incident["start"]), int(incident["duration_seconds"])
    restore_at = start + duration
    edge = incident["edge_id"]; lane_ids = [f"{edge}_{i}" for i in incident["lane_indices"]]
    old = {}
    all_classes = ["private", "emergency", "authority", "army", "vip", "passenger", "hov",
                   "taxi", "bus", "coach", "delivery", "truck", "trailer", "motorcycle",
                   "moped", "bicycle", "pedestrian", "wheelchair", "scooter", "drone",
                   "tram", "rail", "rail_urban", "rail_electric", "rail_fast", "ship", "custom1", "custom2"]
    try:
        while traci.simulation.getMinExpectedNumber() > 0 or traci.simulation.getTime() < float(cfg.get("end", 7200)):
            now = traci.simulation.getTime()
            if now >= start and not old:
                for lane in lane_ids:
                    old[lane] = (traci.lane.getAllowed(lane), traci.lane.getDisallowed(lane))
                    traci.lane.setDisallowed(lane, all_classes)
            if now >= restore_at and old:
                for lane, (allowed, disallowed) in old.items():
                    traci.lane.setAllowed(lane, allowed)
                    traci.lane.setDisallowed(lane, disallowed)
                old.clear()
            if args.plan_routes:
                policies.apply_policy(traci, args.compliance, args.clearance, cfg)
            traci.simulationStep()
            if now >= cfg.get("end", 7200): break
    finally:
        traci.close()
    print(f"Run complete. E1 output files should be in {output} (as configured in the additional file).")
    if args.plan_routes and not policies.IMPLEMENTED:
        print("WARNING: policy hook is not implemented; this is not an intervention result.")


if __name__ == "__main__": main()
