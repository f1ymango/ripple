"""Summarise a bounded P0 replay from its generated files.

Counts and speeds come from ``evaluate.py``. FCD supplies a transparent queue
proxy: sampled vehicles below 5 km/h on audited upstream edges. No missing
observation or unfinished vehicle is treated as zero.
"""

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


KEY_DETECTORS = ("AID01102", "AID01103", "AID01104", "AID01106", "AID01107")
INCIDENT_EDGE = "44419212"
INCIDENT_POS_M = 136.31
RAMP_EDGE = "46766432"
SLOW_MPS = 5 / 3.6


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bin_phase(when, begin):
    second = (datetime.fromisoformat(when) - begin).total_seconds()
    if second < 5400:
        return "pre_incident"
    if second < 7800:
        return "partial_assumed"
    if second < 8100:
        return "mixed_all_transition_0935"
    if second < 9300:
        return "all_assumed"
    if second < 9600:
        return "mixed_reopen_transition_1000"
    return "recovery"


def fcd_phase(second):
    if second < 5400:
        return "pre_incident"
    if second < 7860:
        return "partial_assumed"
    if second < 9420:
        return "all_assumed"
    return "recovery"


def score_rows(evaluation, begin):
    groups = defaultdict(lambda: {"count_bins": 0, "within_5": 0, "observed_count": 0,
                                  "simulated_count": 0, "observed_zero_bins": 0,
                                  "matched_zero_bins": 0, "speed_bins": 0,
                                  "speed_absolute_percentage_error_sum": 0})
    for row in evaluation["count_bins"]:
        phase = bin_phase(row["time"], begin)
        for detector in ("all", row["detector_id"]):
            if detector != "all" and detector not in KEY_DETECTORS:
                continue
            group = groups[(phase, detector)]
            group["count_bins"] += 1
            group["within_5"] += int(row["within_5"])
            group["observed_count"] += row["observed"]
            group["simulated_count"] += row["simulated"]
            if row["observed"] == 0:
                group["observed_zero_bins"] += 1
                group["matched_zero_bins"] += int(row["simulated"] == 0)
    for row in evaluation["speed_bins"]:
        phase = bin_phase(row["time"], begin)
        for detector in ("all", row["detector_id"]):
            if detector != "all" and detector not in KEY_DETECTORS:
                continue
            group = groups[(phase, detector)]
            group["speed_bins"] += 1
            group["speed_absolute_percentage_error_sum"] += row["absolute_percentage_error"]
    result = {}
    for (phase, detector), group in groups.items():
        count_n, speed_n = group["count_bins"], group["speed_bins"]
        result.setdefault(phase, {})[detector] = {
            key: value for key, value in group.items()
            if key != "speed_absolute_percentage_error_sum"
        }
        result[phase][detector]["geh_under_5_percent"] = (
            100 * group["within_5"] / count_n if count_n else None)
        result[phase][detector]["speed_mape_percent"] = (
            group["speed_absolute_percentage_error_sum"] / speed_n if speed_n else None)
    return result


def fcd_queues(fcd, upstream_edges):
    phases = defaultdict(lambda: {"samples": 0, "slow_upstream_sum": 0,
                                 "slow_upstream_peak": 0, "slow_ramp_sum": 0,
                                 "slow_ramp_peak": 0, "ramp_vehicles_sum": 0,
                                 "ramp_vehicles_peak": 0})
    five_minutes = defaultdict(lambda: {"samples": 0, "slow_upstream_sum": 0,
                                        "slow_upstream_peak": 0, "slow_ramp_sum": 0})
    ramp_seen = set()
    for _, timestep in ET.iterparse(fcd, events=("end",)):
        if timestep.tag != "timestep":
            continue
        second = float(timestep.get("time"))
        phase = fcd_phase(second)
        upstream_slow = ramp_slow = ramp_total = 0
        for vehicle in timestep.findall("vehicle"):
            lane = vehicle.get("lane", "")
            edge = lane.rsplit("_", 1)[0]
            speed = float(vehicle.get("speed", "inf"))
            position = float(vehicle.get("pos", "inf"))
            upstream = edge in upstream_edges or (
                edge == INCIDENT_EDGE and position < INCIDENT_POS_M)
            if upstream and speed < SLOW_MPS:
                upstream_slow += 1
            if edge == RAMP_EDGE:
                ramp_total += 1
                ramp_slow += int(speed < SLOW_MPS)
            if vehicle.get("id", "").startswith("f22."):
                ramp_seen.add(int(vehicle.get("id").split(".", 1)[1]))
        group = phases[phase]
        group["samples"] += 1
        group["slow_upstream_sum"] += upstream_slow
        group["slow_upstream_peak"] = max(group["slow_upstream_peak"], upstream_slow)
        group["slow_ramp_sum"] += ramp_slow
        group["slow_ramp_peak"] = max(group["slow_ramp_peak"], ramp_slow)
        group["ramp_vehicles_sum"] += ramp_total
        group["ramp_vehicles_peak"] = max(group["ramp_vehicles_peak"], ramp_total)
        five = five_minutes[int(second // 300) * 300]
        five["samples"] += 1
        five["slow_upstream_sum"] += upstream_slow
        five["slow_upstream_peak"] = max(five["slow_upstream_peak"], upstream_slow)
        five["slow_ramp_sum"] += ramp_slow
        timestep.clear()
    result = {}
    for phase, group in phases.items():
        samples = group["samples"]
        result[phase] = {
            "samples": samples,
            "mean_slow_upstream_vehicles": group["slow_upstream_sum"] / samples,
            "peak_slow_upstream_vehicles": group["slow_upstream_peak"],
            "mean_slow_ramp_vehicles": group["slow_ramp_sum"] / samples,
            "peak_slow_ramp_vehicles": group["slow_ramp_peak"],
            "mean_vehicles_on_ramp": group["ramp_vehicles_sum"] / samples,
            "peak_vehicles_on_ramp": group["ramp_vehicles_peak"],
        }
    five_result = {str(second): {
        "samples": row["samples"],
        "mean_slow_upstream_vehicles": row["slow_upstream_sum"] / row["samples"],
        "peak_slow_upstream_vehicles": row["slow_upstream_peak"],
        "mean_slow_ramp_vehicles": row["slow_ramp_sum"] / row["samples"],
    } for second, row in five_minutes.items()}
    return result, five_result, ramp_seen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("evaluation", "summary", "fcd", "audit", "routes", "network", "loops", "observations", "config", "out"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    begin = datetime.fromisoformat("2026-05-15T07:25:00+08:00")
    upstream = set()
    for path in audit["paths"]:
        if path["leg"] == "main_eastbound" and (
            path["from"], path["to"]) in (("AID01102", "AID01103"), ("AID01103", "AID01104")):
            upstream.update(path["edges"])
    upstream.discard(INCIDENT_EDGE)
    queues, five_minute_queues, ramp_seen = fcd_queues(args.fcd, upstream)
    ramp_flow = next(flow for flow in ET.parse(args.routes).getroot().findall("flow")
                     if flow.find("route").get("edges").split()[0] == RAMP_EDGE)
    output = {
        "purpose": "First bounded assumed P0 diagnostic; no plan benefit or baseline acceptance",
        "assumptions": {"initial_lane": "44419212_0", "onset_hkt": "08:55",
                        "all_lanes_hkt": "09:36", "reopen_hkt": "10:02",
                        "report_times_are_not_physical_transition_observations": True},
        "run_summary": summary,
        "overall_evaluation": {key: value for key, value in evaluation.items()
                               if not isinstance(value, list)},
        "phase_detector_scores": score_rows(evaluation, begin),
        "fcd_queue_proxy": queues,
        "fcd_five_minute_queue_proxy": five_minute_queues,
        "queue_proxy_definition": {
            "slow_threshold_kmh": 5,
            "upstream_edges": sorted(upstream),
            "plus_incident_edge_before_position_m": INCIDENT_POS_M,
            "ramp_edge": RAMP_EDGE,
            "fcd_sample_period_seconds": 10,
            "limitation": "Counts inserted vehicles only; vehicles still waiting outside the network are absent.",
        },
        "ramp_flow": {"id": ramp_flow.get("id"), "scheduled_number": int(ramp_flow.get("number")),
                       "distinct_fcd_vehicles": len(ramp_seen),
                       "seen_ids_are_zero_based_contiguous": (
                           len(ramp_seen) == max(ramp_seen) + 1 if ramp_seen else False),
                       "last_seen_vehicle_index": max(ramp_seen) if ramp_seen else None,
                       "difference_from_scheduled": int(ramp_flow.get("number")) - len(ramp_seen),
                       "limitation": "FCD samples inserted vehicles; the difference from scheduled is supporting, not standalone proof of ramp-specific pending departures."},
        "source_sha256": {name: sha(getattr(args, name)) for name in
                          ("evaluation", "summary", "fcd", "audit", "routes",
                           "network", "loops", "observations", "config")},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
