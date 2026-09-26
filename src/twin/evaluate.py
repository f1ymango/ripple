import argparse
from datetime import datetime
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict

from src.twin.common import load_json, resolve


def geh(m, c):
    return math.sqrt(2 * (m - c) ** 2 / (m + c)) if m + c > 0 else 0.0


def main():
    ap = argparse.ArgumentParser(description="Compare simulated E1 intervals against real 5-minute observations.")
    ap.add_argument("--observations", required=True)
    ap.add_argument("--sim", required=True, help="Directory containing E1 detector XML files")
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", help="Scenario file; supplies observation_start_sim_seconds after warm-up.")
    args = ap.parse_args()
    data = load_json(resolve(args.observations)); sim_dir = resolve(args.sim)
    scenario = load_json(resolve(args.config)) if args.config else {}
    count_rows, speed_rows, speed_errors = [], [], []
    missing_detectors, unmatched_intervals, speed_unavailable_intervals = [], 0, 0
    expected_count_intervals = 0
    unmatched_count_intervals = 0
    vehicle_presence_rows = []
    for d in data["detectors"]:
        observations = d.get("observations", [])
        expected_count_intervals += sum(obs.get("count") is not None for obs in observations)
        lane_files = sorted(sim_dir.glob(f"e1_{d['id']}_*.xml"))
        if not lane_files:
            legacy = sim_dir / f"e1_{d['id']}.xml"
            lane_files = [legacy] if legacy.exists() else []
        if not lane_files:
            missing_detectors.append(d["id"])
            unmatched_count_intervals += sum(obs.get("count") is not None for obs in observations)
            unmatched_intervals += sum(
                obs.get("count") is not None or obs.get("speed_kmh") is not None
                for obs in observations
            )
            continue
        intervals = defaultdict(list)
        for p in lane_files:
            try:
                for item in ET.parse(p).getroot().findall("interval"):
                    intervals[round(float(item.get("begin")), 3)].append(item)
            except ET.ParseError:
                # Keep completed intervals from a run that was explicitly stopped.
                try:
                    for _, item in ET.iterparse(p, events=("end",)):
                        if item.tag == "interval":
                            intervals[round(float(item.get("begin")), 3)].append(item)
                            item.clear()
                except ET.ParseError:
                    pass
        times = [obs.get("time") for obs in observations if obs.get("time")]
        try:
            first_dt = datetime.fromisoformat(times[0].replace("Z", "+00:00")) if times else None
        except ValueError:
            first_dt = None
        first_second = float(data.get("observation_start_sim_seconds",
                                      scenario.get("observation_start_sim_seconds", 0)))
        for obs in observations:
            has_count = obs.get("count") is not None
            has_speed = obs.get("speed_kmh") is not None
            if not has_count and not has_speed:
                continue
            try:
                dt = datetime.fromisoformat(obs["time"].replace("Z", "+00:00")) if obs.get("time") else None
            except ValueError:
                dt = None
            if first_dt and dt:
                sim_second = first_second + (dt - first_dt).total_seconds()
            else:
                sim_second = first_second + float(obs.get("index", 0)) * data.get("interval_seconds", 300)
            items = intervals.get(round(sim_second, 3), [])
            if not items:
                unmatched_intervals += 1
                if has_count:
                    unmatched_count_intervals += 1
                continue

            if has_count:
                measured = sum(float(item.get("nVehContrib", 0)) for item in items)
                score = geh(float(obs["count"]), measured)
                count_rows.append({"detector_id": d["id"], "time": obs.get("time"),
                                   "observed": obs["count"], "simulated": measured,
                                   "geh": score, "within_5": score < 5})
                # A zero observed count is valid closure evidence even though
                # no mean speed exists. Score empty/non-empty state separately.
                observed_empty = float(obs["count"]) == 0
                simulated_empty = measured == 0
                vehicle_presence_rows.append({"detector_id": d["id"], "time": obs.get("time"),
                                              "observed_empty": observed_empty,
                                              "simulated_empty": simulated_empty,
                                              "matched": observed_empty == simulated_empty})

            if has_speed and float(obs["speed_kmh"]) > 0:
                # SUMO E1 XML writes `speed`; accept the older mock `meanSpeed`
                # attribute too. -1 means no vehicle was collected, so no speed
                # comparison exists for that interval.
                valid = [(float(item.get("nVehContrib", 0)),
                          float(item.get("speed", item.get("meanSpeed", -1)))) for item in items]
                valid = [(n, speed) for n, speed in valid if n > 0 and speed >= 0]
                if not valid:
                    speed_unavailable_intervals += 1
                    continue
                simulated_speed = sum(n * speed for n, speed in valid) / sum(n for n, _ in valid) * 3.6
                observed_speed = float(obs["speed_kmh"])
                error = abs(simulated_speed - observed_speed) / observed_speed
                speed_errors.append(error)
                speed_rows.append({"detector_id": d["id"], "time": obs.get("time"),
                                   "observed_kmh": observed_speed,
                                   "simulated_kmh": simulated_speed,
                                   "absolute_percentage_error": 100 * error})

    pct = (100 * sum(r["within_5"] for r in count_rows) / len(count_rows)
           if count_rows else None)
    presence_pct = (100 * sum(r["matched"] for r in vehicle_presence_rows) / len(vehicle_presence_rows)
                    if vehicle_presence_rows else None)
    observed_empty_rows = [r for r in vehicle_presence_rows if r["observed_empty"]]
    empty_match_pct = (100 * sum(r["matched"] for r in observed_empty_rows) / len(observed_empty_rows)
                       if observed_empty_rows else None)
    result = {"count_bins": count_rows, "speed_bins": speed_rows,
              "vehicle_presence_bins": vehicle_presence_rows,
              "geh_under_5_percent": pct,
              "vehicle_presence_match_percent": presence_pct,
              "observed_zero_count_bins": sum(r["observed_empty"] for r in vehicle_presence_rows),
              "observed_zero_count_match_percent": empty_match_pct,
              "speed_mape_percent": 100 * sum(speed_errors) / len(speed_errors) if speed_errors else None,
              "count_bin_n": len(count_rows), "speed_bin_n": len(speed_errors),
              "missing_detector_ids": missing_detectors,
              "unmatched_observation_intervals": unmatched_intervals,
              "unmatched_count_intervals": unmatched_count_intervals,
              "speed_unavailable_intervals": speed_unavailable_intervals,
              "meets_85_percent_target": (pct is not None and pct >= 85
                                          and len(count_rows) == expected_count_intervals
                                          and unmatched_count_intervals == 0)}
    out = resolve(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    details = {k: v for k, v in result.items() if k not in {"count_bins", "speed_bins"}}
    print(json.dumps(details, indent=2)); print(f"Full results: {out}")


if __name__ == "__main__": main()
