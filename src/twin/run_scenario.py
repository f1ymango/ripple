import argparse
import json
import math
import os
import sys
import xml.etree.ElementTree as ET
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
    class MissingFatalTraCIError(Exception):
        pass

    fatal_traci_error = getattr(
        getattr(traci, "exceptions", None), "FatalTraCIError", MissingFatalTraCIError)
    from src.twin import policies
    net, routes = resolve(cfg["network"]), resolve(args.plan_routes or cfg["routes"])
    add = resolve(cfg["detector_additional"])
    output = resolve(cfg.get("output_dir", "sim/work/results")); output.mkdir(parents=True, exist_ok=True)
    begin, end = float(cfg.get("begin", 0)), float(cfg.get("end", 7200))
    configured_end = end
    if args.max_seconds is not None:
        end = min(end, begin + args.max_seconds)
    if end <= begin:
        raise ValueError("Simulation end must be later than begin")
    step_length = float(cfg.get("step_length", 1))
    if not math.isfinite(step_length) or step_length <= 0:
        raise ValueError("step_length must be a finite positive number")
    incident = cfg.get("incident")
    if not isinstance(incident, dict):
        raise ValueError("Scenario must define an incident object")
    start = float(incident["start"])
    duration = float(incident["duration_seconds"])
    if not math.isfinite(start) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("Incident start and duration_seconds must be finite; duration must be positive")
    if start < begin:
        raise ValueError("Incident start must not precede the simulation begin time")
    if args.max_seconds is None and start + duration > end:
        raise ValueError("The complete incident closure must fit within the configured simulation horizon")
    step_count = (end - begin) / step_length
    if not math.isclose(step_count, round(step_count), rel_tol=0, abs_tol=1e-9):
        raise ValueError("Simulation horizon must be an exact multiple of step_length")
    edge_id = str(incident["edge_id"])
    try:
        lane_count = len(__import__("sumolib").net.readNet(str(net)).getEdge(edge_id).getLanes())
    except Exception as exc:
        raise ValueError(f"Incident edge {edge_id!r} is absent from the configured SUMO network") from exc
    phases = incident.get("phases")
    if phases is None:
        phases = [{"offset_seconds": 0, "lane_indices": incident.get("lane_indices")}]
    if not isinstance(phases, list) or not phases:
        raise ValueError("incident.phases must be a non-empty list when provided")
    normalized_phases = []
    previous_offset = -1.0
    for phase in phases:
        if not isinstance(phase, dict):
            raise ValueError("Each incident phase must be an object")
        offset = float(phase.get("offset_seconds", -1))
        selected = phase.get("lane_indices")
        if (not math.isfinite(offset) or offset < 0 or offset >= duration
                or offset <= previous_offset):
            raise ValueError("Incident phase offsets must be increasing, start at 0, and precede incident end")
        previous_offset = offset
        if selected == "all":
            indices = list(range(lane_count))
        elif isinstance(selected, list) and all(
                isinstance(index, int) and not isinstance(index, bool) for index in selected):
            indices = selected
        else:
            raise ValueError(
                "Each incident phase needs lane_indices as explicit zero-based indices or 'all'; "
                "resolve an 'unspecified' lane scope before simulation"
            )
        if (len(set(indices)) != len(indices)
                or any(index < 0 or index >= lane_count for index in indices)):
            raise ValueError(
                f"Incident phase lane indices must be unique and valid for edge {edge_id!r} "
                f"(which has {lane_count} lanes)"
            )
        normalized_phases.append({"offset_seconds": offset, "lane_indices": indices})
    if normalized_phases[0]["offset_seconds"] != 0:
        raise ValueError("The first incident phase must begin at offset_seconds 0")
    if not any(phase["lane_indices"] for phase in normalized_phases):
        raise ValueError("At least one incident phase must close one or more lanes")
    closed_lane_speed = float(cfg.get("incident_lane_speed_mps", 0.0))
    if not math.isfinite(closed_lane_speed) or closed_lane_speed < 0:
        raise ValueError("incident_lane_speed_mps must be a finite nonnegative speed")
    fcd_output = resolve(cfg.get("fcd_output", output / f"{args.label}.fcd.xml"))
    fcd_output.parent.mkdir(parents=True, exist_ok=True)
    statistics_output = output / f"{args.label}.statistics.xml"
    cmd = [require_command("sumo"), "-n", str(net), "-r", str(routes), "-a", str(add),
           "--begin", str(begin), "--end", str(end), "--duration-log.statistics", "true",
           "--statistic-output", str(statistics_output),
           "--max-depart-delay", str(cfg.get("max_depart_delay", -1)),
           "--fcd-output", str(fcd_output), "--device.fcd.period", str(cfg.get("fcd_period", 10)),
           "--tripinfo-output", str(output / f"{args.label}.tripinfo.xml"),
           "--step-length", str(step_length), "--seed", str(cfg.get("seed", 2026)),
           "--no-step-log", "true"]
    traci.start(cmd, label=args.label)
    incident = cfg["incident"]
    start, duration = float(incident["start"]), float(incident["duration_seconds"])
    restore_at = start + duration
    edge = incident["edge_id"]
    old = {}
    steps = int(round(step_count))
    steps_run = 0
    arrived_total = 0
    final_time = begin
    active_lanes = set()
    active_phase = -1
    interrupted = False
    connection_error = None
    try:
        for _ in range(steps):
            now = traci.simulation.getTime()
            if start <= now < restore_at:
                elapsed = now - start
                due_phase = max(i for i, phase in enumerate(normalized_phases)
                                if phase["offset_seconds"] <= elapsed)
                if due_phase != active_phase:
                    desired_lanes = {f"{edge}_{i}" for i in normalized_phases[due_phase]["lane_indices"]}
                    for lane in active_lanes - desired_lanes:
                        traci.lane.setMaxSpeed(lane, old[lane])
                    for lane in desired_lanes - active_lanes:
                        if lane not in old:
                            old[lane] = traci.lane.getMaxSpeed(lane)
                        # Keep route connections available so vehicles queue
                        # before a closed lane instead of losing their route.
                        traci.lane.setMaxSpeed(lane, closed_lane_speed)
                    active_lanes = desired_lanes
                    active_phase = due_phase
            if now >= restore_at and active_lanes:
                for lane in active_lanes:
                    traci.lane.setMaxSpeed(lane, old[lane])
                active_lanes.clear()
            if args.plan_routes:
                policies.apply_policy(traci, args.compliance, args.clearance, cfg)
            traci.simulationStep()
            steps_run += 1
            final_time = traci.simulation.getTime()
            arrived_total += traci.simulation.getArrivedNumber()
            if traci.simulation.getTime() >= end:
                break
    except KeyboardInterrupt:
        interrupted = True
    except fatal_traci_error as exc:
        # SUMO can quit on a fatal route/departure error. Preserve the partial
        # outputs and write an incomplete run summary instead of masking the
        # simulator error with a second failed TraCI query during cleanup.
        interrupted = True
        connection_error = str(exc)
    finally:
        try:
            final_time = traci.simulation.getTime()
            remaining = traci.simulation.getMinExpectedNumber()
            pending_departures = len(traci.simulation.getPendingVehicles())
        except fatal_traci_error as exc:
            connection_error = connection_error or str(exc)
            remaining = pending_departures = None
        try:
            traci.close()
        except fatal_traci_error as exc:
            connection_error = connection_error or str(exc)
    try:
        statistics = ET.parse(statistics_output).getroot()
        vehicle_stats = statistics.find("vehicles")
        teleport_stats = statistics.find("teleports")
        loaded = int(vehicle_stats.get("loaded"))
        departed = int(vehicle_stats.get("inserted"))
        waiting = int(vehicle_stats.get("waiting"))
        teleports = int(teleport_stats.get("total"))
        teleport_reasons = {reason: int(teleport_stats.get(reason, 0))
                            for reason in ("jam", "yield", "wrongLane")}
    except (FileNotFoundError, ET.ParseError, AttributeError, TypeError, ValueError):
        loaded = departed = teleports = None
        waiting = pending_departures
        teleport_reasons = None
    max_depart_delay = cfg.get("max_depart_delay", -1)
    dropped = (max(0, loaded - departed - waiting) if max_depart_delay >= 0
               else 0) if loaded is not None else None
    summary = {"label": args.label, "begin": begin, "requested_end": end, "final_time": final_time,
               "steps": steps_run, "step_budget": steps, "unfinished_at_horizon": remaining,
               "teleports_total": teleports, "teleports_by_reason": teleport_reasons,
               "vehicles_loaded": loaded, "vehicles_departed": departed,
               "vehicles_arrived": arrived_total, "pending_departures": waiting,
               "estimated_dropped_after_departure_delay": dropped,
               "max_depart_delay_seconds": max_depart_delay, "fcd_output": str(fcd_output),
               "statistics_output": str(statistics_output), "statistics_available": loaded is not None,
               "interrupted_by_user": interrupted and connection_error is None,
               "simulator_connection_error": connection_error,
               "complete": not interrupted and final_time >= end,
               "horizon_capped": end < configured_end,
               "scenario_complete": (not interrupted and end >= configured_end and final_time >= configured_end)}
    summary_path = output / f"{args.label}.run-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Run complete at fixed horizon; summary: {summary_path}; FCD: {fcd_output}")
    if args.plan_routes and not policies.IMPLEMENTED:
        print("WARNING: policy hook is not implemented; this is not an intervention result.")


if __name__ == "__main__": main()
