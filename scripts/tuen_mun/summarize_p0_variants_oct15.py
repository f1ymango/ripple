"""Summarize completed P0 variants from original E1 loops and TD observations."""

import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results/tuen-mun-p0-variants-oct15"
OBS = ROOT / "sim/tuen-mun/observations_20260415.json"
WATCH = ("TDS90020", "TDS90024", "TDS90025", "TDS90029", "TDS90032", "TDS90033")


def clock(second):
    minute = 16 * 60 + 30 + int(second // 60)
    return f"{minute // 60:02d}:{minute % 60:02d}"


def loops(run_id):
    counts = defaultdict(float)
    speed_sums = defaultdict(float)
    for path in (ROOT / "sim/work/evaluator" / run_id / "results").glob("e1_*.xml"):
        det = path.name[3:].rsplit("_", 1)[0]
        if det not in WATCH:
            continue
        for row in ET.parse(path).getroot().iter("interval"):
            key = (det, clock(float(row.get("begin"))))
            volume = float(row.get("nVehContrib"))
            counts[key] += volume
            speed = float(row.get("speed"))
            if volume and speed >= 0:
                speed_sums[key] += volume * speed * 3.6
    return {k: {"count": v, "speed_kmh": round(speed_sums[k] / v, 1) if v else None}
            for k, v in counts.items()}


def main():
    observed = {}
    for det in json.loads(OBS.read_text(encoding="utf-8"))["detectors"]:
        if det["id"] in WATCH:
            for row in det["observations"]:
                observed[(det["id"], row["time"][11:16])] = row
    summary = []
    for path in sorted((RES / "runs").glob("*.json")):
        if path.name.endswith(".provenance.json"):
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        run_id = result["run_id"]
        report = json.loads((RES / "evaluator" / f"{run_id}.report.json").read_text(encoding="utf-8"))
        model = loops(run_id)
        profiles = {}
        for det in WATCH:
            profiles[det] = [
                {"time": t, "observed_speed_kmh": observed.get((det, t), {}).get("speed_kmh"),
                 "sim_speed_kmh": model.get((det, t), {}).get("speed_kmh"),
                 "observed_count": observed.get((det, t), {}).get("count"),
                 "sim_count": model.get((det, t), {}).get("count")}
                for t in ("17:50", "18:00", "18:15", "18:30", "18:45", "19:00", "19:30", "19:40")
            ]
        summary.append({"run_id": run_id, "result_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "validation": result["validation"], "health": report["run_health"],
                        "delay_vehicle_hours": result["metrics"]["total_vehicle_hours_delay"],
                        "max_queue_m": result["metrics"]["max_queue_m"],
                        "detector_profiles": profiles})
    out = RES / "p0-variant-profiles.json"
    out.write_text(json.dumps({"source": str(OBS.relative_to(ROOT)).replace("\\", "/"),
                               "bins": "5-minute bin start HKT", "runs": summary}, indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    print(out)


if __name__ == "__main__":
    main()
