"""Compare diagnostic runs on frozen eligible bins, including physical-flow failures."""
import argparse
import json
from collections import defaultdict

from src.twin.common import load_json, resolve
from src.twin.network_sources import sha256


def keyed(rows):
    out = {(row["detector_id"], row["time"]): row for row in rows}
    if len(out) != len(rows):
        raise ValueError("Duplicate detector/time bins")
    return out


def describe(run, common_speed_keys, eligible_speeds):
    evaluation = run["evaluation"]
    counts, speeds = evaluation["count_bins"], keyed(evaluation["speed_bins"])
    stats = run.get("statistics", {})
    vehicles = {k: int(v) for k, v in (stats.get("vehicles") or run["vehicles"]).items()}
    teleports = {k: int(v) for k, v in (stats.get("teleports") or run["teleports"]).items()}
    per_detector = defaultdict(lambda: {"count_bins": 0, "count_pass": 0, "observed": 0.0,
                                      "simulated": 0.0, "speed_ape_sum": 0.0, "speed_bins": 0})
    for row in counts:
        item = per_detector[row["detector_id"]]
        item["count_bins"] += 1
        item["count_pass"] += row["within_5"]
        item["observed"] += row["observed"]
        item["simulated"] += row["simulated"]
    for row in speeds.values():
        item = per_detector[row["detector_id"]]
        item["speed_ape_sum"] += row["absolute_percentage_error"]
        item["speed_bins"] += 1
    for item in per_detector.values():
        item["count_misses"] = item["count_bins"] - item["count_pass"]
        item["speed_mape_percent"] = (item["speed_ape_sum"] / item["speed_bins"]
                                      if item["speed_bins"] else None)
    return {"count_pass": sum(row["within_5"] for row in counts), "count_bins": len(counts),
            "geh_under_5_percent": evaluation["geh_under_5_percent"],
            "speed_mape_percent": evaluation["speed_mape_percent"], "speed_bins": len(speeds),
            "common_speed_bins": len(common_speed_keys),
            "common_speed_mape_percent": (sum(speeds[k]["absolute_percentage_error"] for k in common_speed_keys)
                                           / len(common_speed_keys) if common_speed_keys else None),
            "eligible_speed_bins": eligible_speeds, "unscored_speed_bins": eligible_speeds - len(speeds),
            "missing_detector_ids": evaluation["missing_detector_ids"],
            "unmatched_count_intervals": evaluation["unmatched_count_intervals"],
            "vehicles": vehicles, "waiting_percent": 100 * vehicles["waiting"] / vehicles["loaded"],
            "teleports": teleports, "wall_seconds": run["wall_seconds"],
            "complete": run.get("run_usable", False),
            "per_detector": dict(per_detector),
            "worst_counts": sorted(per_detector, key=lambda d: -per_detector[d]["count_misses"]),
            "worst_speed_contributions": sorted(per_detector, key=lambda d: -per_detector[d]["speed_ape_sum"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--change", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    reference, candidate = [load_json(resolve(p)) for p in (args.reference, args.candidate)]
    for field in ("seed", "simulation_end"):
        if reference[field] != candidate[field]:
            raise ValueError(f"Different {field}")
    for label in ("network", "observations", "loops"):
        if reference["sources"][label]["sha256"] != candidate["sources"][label]["sha256"]:
            raise ValueError(f"Different {label}: this comparison requires fixed physical/observed inputs")
    old, new = [keyed(r["evaluation"]["count_bins"]) for r in (reference, candidate)]
    if old.keys() != new.keys() or any(old[k]["observed"] != new[k]["observed"] for k in old):
        raise ValueError("Count eligibility or observations changed")
    speed_sets = [keyed(r["evaluation"]["speed_bins"]) for r in (reference, candidate)]
    common = set(speed_sets[0]) & set(speed_sets[1])
    if any(speed_sets[0][k]["observed_kmh"] != speed_sets[1][k]["observed_kmh"] for k in common):
        raise ValueError("Measured speed changed")
    # Both diagnostics use the same complete observation export and timestamp grid.
    eligible_speeds = (reference["evaluation"]["speed_bin_n"]
                       + reference["evaluation"]["speed_unavailable_intervals"])
    report = {"change_tested": args.change, "same_count_bins_and_observations": True,
              "reference": describe(reference, common, eligible_speeds),
              "candidate": describe(candidate, common, eligible_speeds),
              "sources": {"reference": {"path": args.reference, "sha256": sha256(resolve(args.reference))},
                          "candidate": {"path": args.candidate, "sha256": sha256(resolve(args.candidate))}},
              "run_sources": {"reference": reference["sources"], "candidate": candidate["sources"]},
              "limitations": ["Count fitting and scoring reuse the same hour: not independent validation.",
                              "An improved GEH percentage is not acceptance of speed, queues or incident replay."]}
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
