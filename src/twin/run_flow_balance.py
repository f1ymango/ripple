"""Run SUMO on the flow-balance inputs with no closure and score it with src/twin/evaluate.py, unchanged.

    python -m src.twin.run_flow_balance --inputs-dir sim/work/flow-balance \\
        --network sim/work/aberdeen.flow-balance.net.xml \\
        --loops sim/work/may-diagnostic/detectors.add.xml \\
        --observations sim/scenarios/detectors.json --out results/twin/oct04-flow-balance.json

`--inputs-dir` is what src/twin/flow_balance_demand.py wrote. The loops and
the observations are Simulation's own files; a loop on an edge that the
network patch cut in two is moved onto the piece it now stands on, at the
same place on the road. The report keeps the evaluator's full output, the
score split between the detectors that set demand and those that only assess
it, and a hash of every input.
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter

from src.twin.common import ROOT, load_json, require_command, resolve
from src.twin.flow_balance_demand import read_net, split_pieces
from src.twin.network_sources import sha256


def _shown(path):
    """A path as the report shows it: from the repository root where it lies inside it."""
    text = str(path)
    return text[len(str(ROOT)) + 1:].replace("\\", "/") if text.startswith(str(ROOT)) else text


def move_loops(loops_path, net, work):
    """Simulation's loops, writing into `work`, moved across any cut edge. Returns the new file."""
    tree = ET.parse(loops_path)
    for loop in tree.getroot().findall("inductionLoop"):
        loop.set("file", str(work / f"e1_{loop.get('id')}.xml"))
        edge, lane = loop.get("lane").rsplit("_", 1)
        pos = float(loop.get("pos"))
        for piece in split_pieces(net, edge):
            first = net.getEdge(edge).getLength()
            if pos > first:
                edge, pos = piece, pos - first
        loop.set("lane", f"{edge}_{lane}")
        loop.set("pos", f"{pos:.2f}")
    out = work / "detectors.add.xml"
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


def split_score(evaluation, demand_setting):
    """GEH and speed error for all detectors, for those that set demand, and for the rest."""
    def part(keep):
        counts = [x for x in evaluation["count_bins"] if keep(x)]
        speeds = [x for x in evaluation["speed_bins"] if keep(x)]
        return {"geh_under_5_percent": round(100 * sum(x["within_5"] for x in counts) / len(counts), 1) if counts else None,
                "count_bins": len(counts),
                "speed_mape_percent": round(sum(x["absolute_percentage_error"] for x in speeds) / len(speeds), 1) if speeds else None,
                "speed_bins": len(speeds)}
    return {"all_detectors": part(lambda x: True),
            "assessment_detectors": part(lambda x: x["detector_id"] not in demand_setting),
            "demand_setting_detectors": part(lambda x: x["detector_id"] in demand_setting)}


def per_detector(evaluation):
    out = {}
    for d in sorted({x["detector_id"] for x in evaluation["count_bins"] + evaluation["speed_bins"]}):
        counts = [x for x in evaluation["count_bins"] if x["detector_id"] == d]
        speeds = [x for x in evaluation["speed_bins"] if x["detector_id"] == d]
        out[d] = {"count_bins": len(counts), "geh_under_5": sum(x["within_5"] for x in counts),
                  "observed_total": round(sum(x["observed"] for x in counts)),
                  "simulated_total": round(sum(x["simulated"] for x in counts)),
                  "speed_bins": len(speeds),
                  "speed_mape_percent": round(sum(x["absolute_percentage_error"] for x in speeds) / len(speeds), 1) if speeds else None}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inputs-dir", required=True)
    ap.add_argument("--network", required=True)
    ap.add_argument("--loops", required=True)
    ap.add_argument("--observations", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--additional", nargs="*", default=[], help="further SUMO additional files")
    ap.add_argument("--summary-only", action="store_true",
                    help="leave the evaluator's bin-by-bin rows out of the report (for a batch of days)")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()
    inputs_dir = resolve(args.inputs_dir)
    build = load_json(inputs_dir / "build.json")
    observed = load_json(resolve(args.observations))
    begin = dt.datetime.fromisoformat(build["begin"])
    first = dt.datetime.fromisoformat(observed["detectors"][0]["observations"][0]["time"])
    obs_start = (first - begin).total_seconds()
    if obs_start < 0 or obs_start % observed["interval_seconds"]:
        raise ValueError("The run must begin a whole number of observation intervals before the first observation")
    slots = int((build["end_seconds"] - obs_start) / observed["interval_seconds"])
    work = inputs_dir / f"run-seed{args.seed}"
    work.mkdir(parents=True, exist_ok=False)
    net = read_net(args.network)
    loops = move_loops(resolve(args.loops), net, work)
    command = [require_command("sumo"), "-n", str(resolve(args.network)), "-r", str(inputs_dir / "demand.rou.xml"),
               "-a", ",".join(map(str, [loops, inputs_dir / "speeds.add.xml"] + [resolve(x) for x in args.additional])),
               "--begin", "0", "--end", str(build["end_seconds"]),
               "--seed", str(args.seed), "--step-length", "1", "--max-depart-delay", "-1",
               "--duration-log.statistics", "true", "--statistic-output", str(work / "statistics.xml"),
               "--no-step-log", "true"]
    started = time.monotonic()
    with (work / "sumo.log").open("w", encoding="utf-8") as log:
        returncode = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout).returncode
    wall = time.monotonic() - started
    if returncode:
        raise RuntimeError(f"SUMO stopped with code {returncode}; see {work / 'sumo.log'}")
    for detector in observed["detectors"]:              # the export is a full ordered grid: keep the run's slots
        detector["observations"] = detector["observations"][:slots]
    (work / "observations.json").write_text(json.dumps(observed), encoding="utf-8")
    (work / "config.json").write_text(json.dumps({"observation_start_sim_seconds": obs_start}), encoding="utf-8")
    subprocess.run([sys.executable, "-m", "src.twin.evaluate", "--config", str(work / "config.json"),
                    "--observations", str(work / "observations.json"), "--sim", str(work),
                    "--out", str(work / "evaluation.json")], check=True, stdout=subprocess.DEVNULL)
    evaluation = load_json(work / "evaluation.json")
    statistics = {child.tag: child.attrib for child in ET.parse(work / "statistics.xml").getroot()}
    log_text = (work / "sumo.log").read_text(encoding="utf-8")
    report = {
        "purpose": "No-closure calibration on flow-balance demand and ordinary-morning speeds; not incident validation",
        "closure_applied": False, "day": build["day"], "ordinary_days": build["ordinary_days"],
        "speeds": build["speeds"], "demand_setting_detectors": build["demand_setting_detectors"],
        "run_begin": build["begin"], "scored_from": first.isoformat(), "scored_slots": slots,
        "seed": args.seed, "additional": args.additional,
        "command": ["sumo"] + [",".join(_shown(x) for x in part.split(",")) for part in command[1:]], "wall_seconds": round(wall, 1),
        "score": split_score(evaluation, set(build["demand_setting_detectors"])),
        "vehicles": statistics["vehicles"], "teleports": statistics["teleports"],
        "teleport_start_lanes": dict(Counter(re.findall(r"Teleporting vehicle .*?lane='([^']+)'", log_text)).most_common()),
        "per_detector": per_detector(evaluation), "build_notes": build["notes"],
        "sources": {label: {"path": _shown(resolve(path)), "sha256": sha256(resolve(path))} for label, path in {
            "network": args.network, "routes": inputs_dir / "demand.rou.xml", "speeds": inputs_dir / "speeds.add.xml",
            "loops": args.loops, "observations": args.observations,
            **{f"additional_{i}": x for i, x in enumerate(args.additional)}}.items()},
        "evaluation": ({k: v for k, v in evaluation.items() if not k.endswith("_bins")}
                       if args.summary_only else evaluation),
    }
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    s, v = report["score"], statistics["vehicles"]
    for key, label in (("all_detectors", "all detectors"), ("assessment_detectors", "assessment only"),
                       ("demand_setting_detectors", "demand-setting")):
        print(f"{label + ':':17s} GEH<5 {s[key]['geh_under_5_percent']}% of {s[key]['count_bins']} bins, "
              f"speed error {s[key]['speed_mape_percent']}% of {s[key]['speed_bins']} bins")
    print(f"vehicles: {v['inserted']} of {v['loaded']} entered, {v['waiting']} waiting; "
          f"teleports {statistics['teleports']['total']}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
