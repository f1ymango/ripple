"""Compare one-input P0 timing sensitivity with the same-input no-closure control."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


WINDOWS = {
    "early_0905_0930": ("09:05", "09:35"),
    "full_0940_0955": ("09:40", "10:00"),
    "recovery_1005_1030": ("10:05", "10:35"),
}
DETECTORS = ("AID01102", "AID01103", "AID01104", "AID01106", "AID01109")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measured(rows, detector, start, end, value):
    return [row[value] for row in rows if row["detector_id"] == detector
            and start <= row["time"][11:16] < end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("p0", "p0_evaluation", "sensitivity", "sensitivity_evaluation",
                 "no_closure", "build", "network", "out"):
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, required=True)
    args = parser.parse_args()
    reports = {"p0_0936": load(args.p0), "sensitivity_0915": load(args.sensitivity),
               "no_closure": load(args.no_closure)}
    evaluations = {"p0_0936": load(args.p0_evaluation),
                   "sensitivity_0915": load(args.sensitivity_evaluation),
                   "no_closure": reports["no_closure"]["evaluation"]}
    # The diagnostic JSON names the evaluation hash; the observed pair check is
    # explicit, so a different eligible-bin set cannot masquerade as a comparison.
    pair = lambda d: [(r["detector_id"], r["time"], r["observed"])
                      for r in d["count_bins"]]
    if not (pair(evaluations["p0_0936"]) == pair(evaluations["sensitivity_0915"])
            == pair(evaluations["no_closure"])):
        raise ValueError("Runs do not share the same eligible observed count bins")
    build = load(args.build)
    chain = build["plan"]["main_eastbound"]
    incident_index = chain["edges"].index("44419212")
    downstream_joins = [origin for origin in chain["origins"]
                        if origin.get("pair") == "AID01104->AID01106"
                        and origin["start"] > incident_index]
    net = ET.parse(args.network).getroot()
    ramp_tls = next((connection.get("tl") for connection in net.findall("connection")
                     if connection.get("from") == "46766432" and connection.get("tl")), None)
    signal = next((logic for logic in net.findall("tlLogic") if logic.get("id") == ramp_tls), None)
    merge = [connection.attrib for connection in net.findall("connection")
             if connection.get("to") == "1194711693"
             and connection.get("from") in ("485146396", "462275986#1")]
    output = {
        "purpose": "Compare source-identical diagnostic variants; no physical phase is established by fit",
        "same_eligible_count_pairs": True,
        "eligible_count_bins": len(pair(evaluations["p0_0936"])),
        "variants": {},
        "network_findings": {
            "incident_edge_index_in_main_eastbound_plan": incident_index,
            "joins_after_incident_before_AID01106": downstream_joins,
            "ramp_signal_id": ramp_tls,
            "ramp_signal_phases": [phase.attrib for phase in signal.findall("phase")] if signal is not None else [],
            "merge_connections": merge,
        },
        "source_sha256": {name: sha(getattr(args, name)) for name in
                          ("p0", "p0_evaluation", "sensitivity",
                           "sensitivity_evaluation", "no_closure", "build", "network")},
    }
    for name, report in reports.items():
        evaluation = evaluations[name]
        vehicle = (report["vehicles"] if name == "no_closure"
                   else report["run_summary"])
        teleport = (int(report["teleports"]["total"]) if name == "no_closure"
                    else report["run_summary"]["teleports_total"])
        variant = {
            "geh_under_5_percent": evaluation["geh_under_5_percent"],
            "speed_mape_percent": evaluation["speed_mape_percent"],
            "waiting_at_horizon": int(vehicle["waiting"] if name == "no_closure"
                                      else vehicle["pending_departures"]),
            "teleports": teleport,
            "windows": {},
        }
        for label, (start, end) in WINDOWS.items():
            variant["windows"][label] = {}
            for detector in DETECTORS:
                observed = measured(evaluation["count_bins"], detector, start, end, "observed")
                simulated = measured(evaluation["count_bins"], detector, start, end, "simulated")
                observed_speed = measured(evaluation["speed_bins"], detector, start, end, "observed_kmh")
                simulated_speed = measured(evaluation["speed_bins"], detector, start, end, "simulated_kmh")
                variant["windows"][label][detector] = {
                    "eligible_count_bins": len(observed),
                    "observed_count": sum(observed), "simulated_count": sum(simulated),
                    "observed_speed_kmh_range": [min(observed_speed), max(observed_speed)] if observed_speed else None,
                    "simulated_speed_kmh_range": [min(simulated_speed), max(simulated_speed)] if simulated_speed else None,
                }
        output["variants"][name] = variant
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
