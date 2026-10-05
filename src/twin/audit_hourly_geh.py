"""Score hourly-equivalent GEH from the same eligible five-minute count bins.

An archive gap makes this an extrapolation from eligible bins, not a measured
complete-hour total. The script retains each detector's bin count and both
unscaled and scaled GEH so the distinction is visible.
"""
import argparse
import json
import math
from collections import defaultdict

from src.twin.common import load_json, resolve
from src.twin.network_sources import sha256


def by_detector(rows):
    bins = {}
    for row in rows:
        key = (row["detector_id"], row["time"])
        if key in bins:
            raise ValueError(f"Duplicate count bin: {key}")
        pair = (float(row["observed"]), float(row["simulated"]))
        if any(not math.isfinite(value) or value < 0 for value in pair):
            raise ValueError(f"Counts must be finite and nonnegative: {key}")
        bins[key] = pair
    return bins


def geh(observed, simulated):
    if observed < 0 or simulated < 0:
        raise ValueError("Counts must be nonnegative")
    return math.sqrt(2 * (simulated - observed) ** 2 / (simulated + observed)) if observed + simulated else 0.0


def score(rows, expected_bins=12):
    grouped = defaultdict(list)
    for (detector, _), pair in rows.items():
        grouped[detector].append(pair)
    output = {}
    for detector, pairs in sorted(grouped.items()):
        n = len(pairs)
        if n > expected_bins:
            raise ValueError(f"Too many bins for {detector}: {n}")
        observed, simulated = (sum(pair[i] for pair in pairs) for i in (0, 1))
        factor = expected_bins / n
        output[detector] = {
            "eligible_bins": n,
            "missing_or_ineligible_bins": expected_bins - n,
            "observed_in_eligible_bins": observed,
            "simulated_in_eligible_bins": simulated,
            "observed_hourly_equivalent": observed * factor,
            "simulated_hourly_equivalent": simulated * factor,
            "geh_on_eligible_bin_sums": geh(observed, simulated),
            "geh_hourly_equivalent": geh(observed * factor, simulated * factor),
        }
        output[detector]["under_5_hourly_equivalent"] = output[detector]["geh_hourly_equivalent"] < 5
    passed = sum(row["under_5_hourly_equivalent"] for row in output.values())
    return {"detectors_under_5": passed, "detectors_scored": len(output),
            "under_5_percent": 100 * passed / len(output) if output else None,
            "by_detector": output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    reports = {label: load_json(resolve(path)) for label, path in
               (("reference", args.reference), ("candidate", args.candidate))}
    sources = {}
    rows = {}
    for label, path in (("reference", args.reference), ("candidate", args.candidate)):
        report = reports[label]
        if report.get("closure_applied") is True or report.get("run_usable") is False:
            raise ValueError(f"{label} is not a complete no-closure result")
        if report["evaluation"]["unmatched_count_intervals"]:
            raise ValueError(f"{label} has unmatched count intervals")
        rows[label] = by_detector(report["evaluation"]["count_bins"])
        sources[label] = {"path": path, "sha256": sha256(resolve(path)),
                          "observations_sha256": report["sources"]["observations"]["sha256"]}
    if sources["reference"]["observations_sha256"] != sources["candidate"]["observations_sha256"]:
        raise ValueError("Different observation exports")
    if rows["reference"].keys() != rows["candidate"].keys():
        raise ValueError("Different eligible detector/time bins")
    if any(rows["reference"][key][0] != rows["candidate"][key][0] for key in rows["reference"]):
        raise ValueError("Observed count changed")
    report = {"method": "For each detector, sum eligible five-minute bins, multiply both observed and simulated sums by 12/eligible_bins, then calculate GEH on those hourly equivalents.",
              "interval_seconds": 300, "expected_bins_per_detector": 12,
              "not_a_measured_full_hour": True, "eligible_count_pairs_identical": True,
              "sources": sources, "reference": score(rows["reference"]),
              "candidate": score(rows["candidate"])}
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Hourly-equivalent GEH: {report['reference']['detectors_under_5']}/"
          f"{report['reference']['detectors_scored']} reference, "
          f"{report['candidate']['detectors_under_5']}/"
          f"{report['candidate']['detectors_scored']} candidate -> {out}")


if __name__ == "__main__":
    main()
