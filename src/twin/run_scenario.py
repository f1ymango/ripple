import argparse
import json
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
    ap.add_argument("--max-seconds", type=int, help="Hard wall on simulated seconds; never drains an unbounded vehicle queue.")
    args = ap.parse_args()
    cfg = load_json(resolve(args.config))
    import traci
    from src.twin import policies
    net, routes = resolve(cfg["network"]), resolve(args.plan_routes or cfg["routes"])
    add = resolve(cfg["detector_additional"])
    output = resolve(cfg.get("output_dir", "sim/work/results")); output.mkdir(parents=True, exist_ok=True)
    begin, end = float(cfg.get("begin", 0)), float(cfg.get("end", 7200))
    if args.max_seconds is not None:
        end = min(end, begin + args.max_seconds)
    if end <= begin:
        raise ValueError("Simulation end must be later than begin")
    fcd_output = resolve(cfg.get("fcd_output", output / f"{args.label}.fcd.xml"))
    fcd_output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [require_command("sumo"), "-n", str(net), "-r", str(routes), "-a", str(add),
           "--begin", str(begin), "--end", str(end), "--duration-log.statistics", "true",
           "--max-depart-delay", str(cfg.get("max_depart_delay", 60)),
           "--fcd-output", str(fcd_output), "--device.fcd.period", str(cfg.get("fcd_period", 10)),
           "--tripinfo-output", str(output / f"{args.label}.tripinfo.xml"),
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
    steps = int((end - begin) / float(cfg.get("step_length", 1)))
    interrupted = False
    try:
        for _ in range(steps):
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
            if traci.simulation.getTime() >= end:
                break
    except KeyboardInterrupt:
        interrupted = True
    finally:
        final_time = traci.simulation.getTime()
        remaining = traci.simulation.getMinExpectedNumber()
        try:
            teleports = traci.simulation.getStartingTeleportNumber()
        except (AttributeError, Exception):
            teleports = None
        loaded = traci.simulation.getLoadedNumber()
        departed = traci.simulation.getDepartedNumber()
        arrived = traci.simulation.getArrivedNumber()
        pending_departures = len(traci.simulation.getPendingVehicles())
        dropped = max(0, loaded - departed - pending_departures)
        traci.close()
    summary = {"label": args.label, "begin": begin, "requested_end": end, "final_time": final_time,
               "steps": steps, "unfinished_at_horizon": remaining, "teleports_started": teleports,
               "vehicles_loaded": loaded, "vehicles_departed": departed,
               "vehicles_arrived": arrived, "pending_departures": pending_departures,
               "estimated_dropped_after_departure_delay": dropped,
               "max_depart_delay_seconds": cfg.get("max_depart_delay", 60), "fcd_output": str(fcd_output),
               "interrupted_by_user": interrupted, "complete": not interrupted and final_time >= end}
    summary_path = output / f"{args.label}.run-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Run complete at fixed horizon; summary: {summary_path}; FCD: {fcd_output}")
    if args.plan_routes and not policies.IMPLEMENTED:
        print("WARNING: policy hook is not implemented; this is not an intervention result.")


if __name__ == "__main__": main()
