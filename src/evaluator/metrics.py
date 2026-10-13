"""The contract's metrics, each read from SUMO output files. Nothing is estimated here.

Vehicles are in scope when they were scheduled to depart at or after the end
of the warm-up. That includes vehicles still driving, and still waiting to
enter, when the run ends: leaving them out would make a plan that strands
more traffic look better.
"""
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from src import validation_targets as targets
from src.evaluator.behaviour import LEFT_FILE
from src.evaluator.scenario import BIN_SECONDS
from src.twin.common import ROOT

QUEUE_JOIN_GAP_M = 10.0     # a lane's queue reaches the next edge upstream if it ends this close to the lane start
TELEPORT_AFTER_SECONDS = 300    # SUMO's default --time-to-teleport; simulate.py does not change it
AT_LANE_SHUT_SECONDS = 60       # a wrong-lane wait that began this soon after a lane shut is caused by the shutting
WRONG_LANE_TELEPORT = re.compile(r"Teleporting vehicle '([^']+)'; waited too long \(wrong lane\), "
                                 r"lane='([^']+)', time=(\d+(?:\.\d+)?)")
DEFINITIONS = {
    "total_vehicle_hours_delay": "Sum over in-scope vehicles of SUMO timeLoss (time lost against each "
                                 "vehicle's own free speed) plus departDelay (time waiting to enter), up to the end of the run. "
                                 "A vehicle that left the corridor because of the queue also counts the scenario's "
                                 "extra_minutes_outside, an assumption, and any time it waited outside the network; "
                                 "the run report gives that part separately.",
    "delay_vs_do_nothing_pct": "Change in total_vehicle_hours_delay against the P0 run of the same scenario, "
                               "compliance and clearance; zero for P0.",
    "max_queue_m": "Per named path: largest distance over the run from the downstream end of the path's first edge "
                   "back to the last waiting vehicle, following SUMO's queue output upstream edge by edge "
                   "for as long as each edge's queue reaches its upstream end. Sampled every 10 seconds. "
                   "It cannot exceed the path's length: near 100% in queue_share_of_path_pct means the queue ran off the path.",
    "corridor_tt_p95_min": "95th percentile (nearest rank) of time in the network for in-scope vehicles on the "
                           "scenario's corridor route. A vehicle still driving at the end counts with its time so far; "
                           "one that left the corridor at an exit is not counted.",
    "emergency_tt_min": "Length of each emergency-route edge divided by the mean speed of all traffic on it from "
                        "closure onset to the end of the run, summed. An edge no vehicle used counts at its speed limit. "
                        "General traffic, not blue-light running.",
    "co2_kg": "Sum of SUMO's CO2 for in-scope vehicles, default emission class for every vehicle. "
              "Vehicles waiting outside the network emit nothing.",
    "residential_delay_share_pct": "Share of all edge timeLoss after the warm-up that falls on edges of the "
                                   "scenario's residential types. Excludes time waiting to enter.",
    "vehicles_completed": "In-scope vehicles that finished their trip in the network before the run ended. "
                          "A vehicle that left the corridor because of the queue did not.",
    "validation": "src/twin/evaluate.py, unchanged, over every observed bin after the warm-up (P0 only), "
                  "rounded to two decimals towards failing. speed_mape_free_flow_pct uses only speed bins the "
                  "detector measured at 30 km/h or more; congestion_state_agreement_pct is the share of speed bins "
                  "where model and detector are on the same side of 30 km/h; "
                  "wrong_lane_teleports_not_at_lane_shut counts SUMO wrong-lane teleports whose wait did not begin "
                  "within 60 seconds after a lane shut (src/validation_targets.py).",
}


def flow_routes(routes_path):
    """Flow id to its fixed list of edges. A vehicle id is '<flow id>.<n>'."""
    return {flow.get("id"): flow.find("route").get("edges").split()
            for flow in ET.parse(routes_path).getroot().iter("flow")}


def trips(tripinfo_path, warmup, end):
    """In-scope vehicles with seconds lost, seconds in the network, CO2 in mg and whether they arrived."""
    out = []
    for _, node in ET.iterparse(tripinfo_path):
        if node.tag != "tripinfo":
            continue
        entered, wait = float(node.get("depart")), float(node.get("departDelay"))
        scheduled = (entered if entered >= 0 else end) - wait
        if scheduled >= warmup:
            out.append({"id": node.get("id"), "flow": node.get("id").rsplit(".", 1)[0], "entered": entered >= 0,
                        "arrived": float(node.get("arrival")) >= 0,
                        "in_network_s": float(node.get("duration")),
                        "time_loss_s": float(node.get("timeLoss")), "entry_wait_s": wait,
                        "co2_mg": float(node.find("emissions").get("CO2_abs"))})
        node.clear()
    return out


def left_corridor(work, warmup):
    """Vehicles that left because of the queue (behaviour.py): ids that took an exit, and in-scope ones kept out."""
    path = Path(work) / LEFT_FILE
    rows = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    at_exit = {row["id"] for row in rows if row["how"] == "exit"}
    kept_out = [row for row in rows if row["how"] == "entry" and row["second"] - row["waited_seconds"] >= warmup]
    return at_exit, kept_out


def percentile95(values):
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def max_queue(queues_path, path_edges, net):
    """Largest back-of-queue distance (m) along `path_edges`, listed from the queue head upstream."""
    lengths = {edge: net.getEdge(edge).getLength() for edge in path_edges}
    longest = 0.0
    for _, sample in ET.iterparse(queues_path):
        if sample.tag != "data":
            continue
        by_edge = {}
        for lane in sample.iter("lane"):
            edge = lane.get("id").rsplit("_", 1)[0]
            by_edge[edge] = max(by_edge.get(edge, 0.0), float(lane.get("queueing_length")))
        total = 0.0
        for edge in path_edges:
            queued = min(by_edge.get(edge, 0.0), lengths[edge])
            total += queued
            if queued < lengths[edge] - QUEUE_JOIN_GAP_M:
                break
        longest = max(longest, total)
        sample.clear()
    return longest


def edge_totals(edges_path, since=0):
    """Per edge from `since`: seconds of vehicle presence, metres driven, seconds lost."""
    totals = {}
    for _, interval in ET.iterparse(edges_path):
        if interval.tag != "interval":
            continue
        if float(interval.get("begin")) >= since:
            for edge in interval.iter("edge"):
                seconds = float(edge.get("sampledSeconds"))
                row = totals.setdefault(edge.get("id"), [0.0, 0.0, 0.0])
                row[0] += seconds
                row[1] += seconds * float(edge.get("speed"))
                row[2] += float(edge.get("timeLoss"))
        interval.clear()
    return totals


def score_against_detectors(work, observations_path, warmup):
    """Simulation's scorer, unchanged, on this run's loop output."""
    work = Path(work)
    (work / "evaluate-config.json").write_text(
        json.dumps({"observation_start_sim_seconds": warmup}), encoding="utf-8")
    loops = next(ET.parse(work / "detectors.add.xml").getroot().iter("inductionLoop"))
    subprocess.run([sys.executable, "-m", "src.twin.evaluate", "--observations", str(observations_path),
                    "--sim", str((work / loops.get("file")).parent),
                    "--config", str(work / "evaluate-config.json"),
                    "--out", str(work / "evaluation.json")],
                   check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    return json.loads((work / "evaluation.json").read_text(encoding="utf-8"))


def read_net(path):
    import sumolib
    return sumolib.net.readNet(str(path))


def compute(scenario, files, work, net):
    """(contract metrics without the baseline comparison, detail for the run report)."""
    work, measure, run = Path(work), scenario["metrics"], scenario["run"]
    vehicles = trips(work / "tripinfo.xml", run["warmup_seconds"], run["end_seconds"])
    took_exit, kept_out = left_corridor(work, run["warmup_seconds"])
    for v in vehicles:
        v["left"] = v["id"] in took_exit
    left_at_exit = sum(v["left"] for v in vehicles)
    outside_h = ((left_at_exit + len(kept_out)) * scenario.get("drivers_leave", {}).get("extra_minutes_outside", 0) / 60
                 + sum(row["waited_seconds"] for row in kept_out) / 3600)
    routes = flow_routes(files["routes"])
    corridor = measure["corridor"]
    on_corridor = [v for v in vehicles if v["entered"] and not v["left"]
                   and routes[v["flow"]][0] == corridor["from_edge"]
                   and routes[v["flow"]][-1] == corridor["to_edge"]
                   and corridor["via_edge"] in routes[v["flow"]]]
    if not on_corridor:
        raise ValueError("No vehicle used the scenario's corridor route; corridor travel time is undefined")
    all_edges = edge_totals(work / "edges.xml")
    lost = sum(row[2] for row in all_edges.values())
    residential = sum(row[2] for edge, row in all_edges.items()
                      if net.getEdge(edge).getType() in measure["residential_edge_types"])
    during = edge_totals(work / "edges.xml", since=scenario["closure"]["onset_seconds"])
    emergency_s, used = 0.0, 0
    for edge_id in measure["emergency_route_edges"]:
        edge, row = net.getEdge(edge_id), during.get(edge_id)
        moving = row is not None and row[1] > 0
        used += moving
        emergency_s += edge.getLength() / (row[1] / row[0] if moving else edge.getSpeed())
    time_loss_h = sum(v["time_loss_s"] for v in vehicles) / 3600
    entry_wait_h = sum(v["entry_wait_s"] for v in vehicles) / 3600
    wait_by_entry = {}
    for v in vehicles:
        entry = routes[v["flow"]][0]
        wait_by_entry[entry] = wait_by_entry.get(entry, 0.0) + v["entry_wait_s"] / 3600
    queues = {name: max_queue(work / "queues.xml", path, net)
              for name, path in sorted(measure["queue_paths"].items())}
    path_m = {name: sum(net.getEdge(edge).getLength() for edge in path)
              for name, path in measure["queue_paths"].items()}
    metrics = {
        "total_vehicle_hours_delay": round(time_loss_h + entry_wait_h + outside_h, 1),
        "max_queue_m": {name: round(length) for name, length in queues.items()},
        "corridor_tt_p95_min": round(percentile95([v["in_network_s"] for v in on_corridor]) / 60, 1),
        "emergency_tt_min": round(emergency_s / 60, 1),
        "co2_kg": round(sum(v["co2_mg"] for v in vehicles) / 1e6),
        "residential_delay_share_pct": round(100 * residential / lost, 1) if lost else 0.0,
        "vehicles_completed": sum(v["arrived"] and not v["left"] for v in vehicles),
    }
    detail = {
        "vehicles_in_scope": len(vehicles) + len(kept_out),
        "vehicles_in_scope_left_corridor": {"at_an_exit": left_at_exit, "kept_out_of_the_network": len(kept_out)},
        "delay_hours_assumed_outside_network": round(outside_h, 1),
        "vehicles_in_scope_still_driving": sum(v["entered"] and not v["arrived"] for v in vehicles),
        "vehicles_in_scope_never_entered": sum(not v["entered"] for v in vehicles),
        "delay_hours_in_network": round(time_loss_h, 1),
        "delay_hours_waiting_to_enter": round(entry_wait_h, 1),
        "delay_hours_waiting_to_enter_by_entry_edge": {edge: round(hours, 1) for edge, hours in sorted(
            wait_by_entry.items(), key=lambda item: -item[1])[:5] if round(hours, 1)},
        "queue_path_m": {name: round(length) for name, length in sorted(path_m.items())},
        "queue_share_of_path_pct": {name: round(100 * length / path_m[name], 1)
                                    for name, length in queues.items()},
        "corridor_vehicles": len(on_corridor),
        "corridor_vehicles_still_driving": sum(not v["arrived"] for v in on_corridor),
        "emergency_route_edges": len(measure["emergency_route_edges"]),
        "emergency_route_edges_with_traffic": used,
        "measurement_bin_seconds": BIN_SECONDS,
    }
    return metrics, detail


def validation(evaluation, wrong_lane_not_at_lane_shut):
    """The contract's validation block, version 2 (src/validation_targets.py).

    Rounded so that rounding can never turn a miss into a pass. The speed
    error over free-flow bins uses only bins the detector measured at 30 km/h
    or more; congestion-state agreement is the share of speed bins where model
    and detector are on the same side of 30 km/h.
    """
    rows = evaluation["speed_bins"]
    free = [r["absolute_percentage_error"] for r in rows if r["observed_kmh"] >= targets.CONGESTED_KMH]
    agree = sum((r["observed_kmh"] < targets.CONGESTED_KMH) == (r["simulated_kmh"] < targets.CONGESTED_KMH)
                for r in rows)
    if not free or not rows:
        raise ValueError("No speed bin to validate against; the detector data has no measured speed")
    return {"geh_under_5_pct": math.floor(evaluation["geh_under_5_percent"] * 100) / 100,
            "speed_mape_pct": math.ceil(evaluation["speed_mape_percent"] * 100) / 100,
            "speed_mape_free_flow_pct": math.ceil(sum(free) / len(free) * 100) / 100,
            "congestion_state_agreement_pct": math.floor(10000 * agree / len(rows)) / 100,
            "wrong_lane_teleports_not_at_lane_shut": len(wrong_lane_not_at_lane_shut)}


def wrong_lane_teleports(log_text, closure_steps):
    """SUMO's wrong-lane teleports split into (stuck from the moment a lane shut, every other one).

    SUMO teleports a vehicle that has stood still for TELEPORT_AFTER_SECONDS,
    so its wait began that long before the teleport. A wait that began within
    AT_LANE_SHUT_SECONDS after a lane shut is a driver caught in that lane
    when it closed; any other wrong-lane teleport means the model left a driver
    unable to reach its lane. Each entry is 'vehicle lane second'.
    """
    shut, closed = [], set()
    for step in closure_steps:
        now = set(step["lanes_closed"])
        if now - closed:
            shut.append(step["second"])
        closed = now
    at_shut, other = [], []
    for vehicle, lane, second in WRONG_LANE_TELEPORT.findall(log_text):
        began = float(second) - TELEPORT_AFTER_SECONDS
        entry = f"{vehicle} {lane} {float(second):g}"
        (at_shut if any(s <= began <= s + AT_LANE_SHUT_SECONDS for s in shut) else other).append(entry)
    return at_shut, other


def speed_error_by_source(evaluation, assessed):
    """Speed error where the model makes the speed itself (`assessed` detectors), and everywhere else.

    Elsewhere the speed is set by a sign (speed_signs.py), so the error there
    says how well the sign's source predicts the morning, not how well the
    model does.
    """
    def part(rows):
        return {"speed_bins": len(rows),
                "speed_mape_pct": round(sum(r["absolute_percentage_error"] for r in rows) / len(rows), 2) if rows else None}
    rows = evaluation["speed_bins"]
    return {"detectors_where_the_model_makes_the_speed": sorted(assessed),
            "model_makes_the_speed": part([r for r in rows if r["detector_id"] in assessed]),
            "speed_set_by_a_sign": part([r for r in rows if r["detector_id"] not in assessed])}


def by_phase(evaluation, scenario, clearance_min):
    """The detector score split into before, during and after the assumed closure."""
    from datetime import datetime, timedelta
    begin = datetime.fromisoformat(scenario["run"]["begin"])
    onset = begin + timedelta(seconds=scenario["closure"]["onset_seconds"])
    reopen = onset + timedelta(minutes=clearance_min)

    def phase(row):
        time = datetime.fromisoformat(row["time"])
        return ("before_closure" if time + timedelta(seconds=BIN_SECONDS) <= onset
                else "after_reopening" if time >= reopen else "during_closure")
    out = {}
    for name in ("before_closure", "during_closure", "after_reopening"):
        counts = [r for r in evaluation["count_bins"] if phase(r) == name]
        speeds = [r for r in evaluation["speed_bins"] if phase(r) == name]
        out[name] = {
            "count_bins": len(counts),
            "geh_under_5_pct": round(100 * sum(r["within_5"] for r in counts) / len(counts), 2) if counts else None,
            "speed_bins": len(speeds),
            "speed_mape_pct": round(sum(r["absolute_percentage_error"] for r in speeds) / len(speeds), 2) if speeds else None,
        }
    return out
