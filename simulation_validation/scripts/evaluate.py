import argparse
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict

from common import load_json, resolve


def geh(m, c):
    return math.sqrt(2 * (m - c) ** 2 / (m + c)) if m + c > 0 else 0.0


def main():
    ap = argparse.ArgumentParser(description="Compare simulated E1 intervals against real 5-minute observations.")
    ap.add_argument("--observations", required=True)
    ap.add_argument("--sim", required=True, help="Directory containing E1 detector XML files")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = load_json(resolve(args.observations)); sim_dir = resolve(args.sim)
    count_rows, speed_errors = [], []
    for d in data["detectors"]:
        p = sim_dir / f"e1_{d['id']}.xml"
        if not p.exists(): continue
        intervals = {}
        for item in ET.parse(p).getroot().findall("interval"):
            intervals[round(float(item.get("begin")), 3)] = item
        # Observation timestamp is matched by sequence to simulated interval index.
        for i, obs in enumerate(d.get("observations", [])):
            if obs.get("count") is None or obs.get("speed_kmh") is None: continue
            # SUMO output starts at simulation time 0; observation entries are ordered in time.
            item = intervals.get(round(i * data.get("interval_seconds", 300), 3))
            if item is None: continue
            measured = float(item.get("nVehContrib", 0))
            speed = float(item.get("meanSpeed", 0)) * 3.6
            count_rows.append({"detector_id": d["id"], "time": obs.get("time"), "observed": obs["count"], "simulated": measured,
                               "geh": geh(float(obs["count"]), measured), "within_5": geh(float(obs["count"]), measured) < 5})
            if float(obs["speed_kmh"]): speed_errors.append(abs(speed - float(obs["speed_kmh"])) / abs(float(obs["speed_kmh"])))
    if not count_rows: raise ValueError("No matched count intervals. Check E1 XML output, detector IDs, and interval alignment.")
    pct = 100 * sum(r["within_5"] for r in count_rows) / len(count_rows)
    result = {"count_bins": count_rows, "geh_under_5_percent": pct,
              "speed_mape_percent": 100 * sum(speed_errors) / len(speed_errors) if speed_errors else None,
              "count_bin_n": len(count_rows), "speed_bin_n": len(speed_errors),
              "meets_85_percent_target": pct >= 85}
    out = resolve(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "count_bins"}, indent=2)); print(f"Full results: {out}")


if __name__ == "__main__": main()
