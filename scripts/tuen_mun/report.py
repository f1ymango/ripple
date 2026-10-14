"""Tuen Mun matched comparison: P0, P1 and P2 per cell, E's delay and the delay with Castle Peak Road's longer drive charged.

    python scripts/tuen_mun/report.py --results-dir results/tuen-mun --plan-set rehearsal --label replay-v2 \\
        [--outside 0 4 10]
    -> printed table and <results-dir>/comparison.json

E's delay is SUMO timeLoss plus waiting to enter, plus extra_minutes_outside for each driver who left at
Ting Kau. timeLoss is time lost against the road the car is on, so a car sent round Castle Peak Road loses
nothing for the extra distance at 50-70 km/h. For each car whose trip was longer than its flow's normal
route, this adds (its ideal driving time) - (the normal route's ideal time), both SUMO's own
duration - timeLoss, the normal one from the same flow's cars before the crash in that cell's P0.
`--outside` recomputes the total for other minutes charged per driver who left.
"""
import argparse
import glob
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "sim/work/evaluator"
CRASH_ONSET_S = 4680


def trips(run_id):
    out = {}
    for _, n in ET.iterparse(WORK / run_id / "tripinfo.xml"):
        if n.tag == "tripinfo":
            out[n.get("id")] = {k: float(n.get(k)) for k in ("depart", "departDelay", "arrival", "duration",
                                                            "routeLength", "timeLoss")}
        n.clear()
    return out


def left(run_id):
    p = WORK / run_id / "left-corridor.json"
    return {r["id"] for r in json.loads(p.read_text())} if p.exists() else set()


def normal_trips(t0, gone):
    """Per flow: the median route length and ideal driving time of its cars that set off before the crash."""
    by = defaultdict(list)
    for v, t in t0.items():
        if t["arrival"] >= 0 and 1800 <= t["depart"] < CRASH_ONSET_S and v not in gone:
            by[v.rsplit(".", 1)[0].split(".")[0]].append(t)
    return {f: (statistics.median(x["routeLength"] for x in ts), statistics.median(x["duration"] - x["timeLoss"] for x in ts))
            for f, ts in by.items() if ts}


def extra_driving(t, normal):
    """Hours of extra ideal driving for cars whose route was longer than their flow's normal one."""
    hours, cars = 0.0, 0
    for v, x in t.items():
        f = v.rsplit(".", 1)[0].split(".")[0]
        if f in normal and x["arrival"] >= 0 and x["routeLength"] > normal[f][0] + 200:
            cars += 1
            hours += max(0.0, (x["duration"] - x["timeLoss"]) - normal[f][1]) / 3600
    return hours, cars


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--plan-set", required=True)
    parser.add_argument("--label", required=True, help="run_label of the frozen scenario; cells are its seed variants")
    parser.add_argument("--outside", type=float, nargs="*", default=[0, 4, 10])
    args = parser.parse_args()
    res = ROOT / args.results_dir
    runs = {}
    for p in glob.glob(str(res / "runs" / "*.json")):
        if p.endswith(".provenance.json"):
            continue
        r = json.loads(Path(p).read_text())
        parts = r["run_id"].split("_")       # date_TMR_plan_cNN_tNN_label_planset
        if parts[-1] != args.plan_set or not parts[-2].startswith(args.label):
            continue
        runs[(parts[-2], parts[3], parts[2])] = r
    cells = sorted({(label, c) for label, c, _ in runs})
    out = []
    for label, c in cells:
        if not all((label, c, p) in runs for p in ("P0", "P1", "P2")):
            continue
        r = {p: runs[(label, c, p)] for p in ("P0", "P1", "P2")}
        t = {p: trips(r[p]["run_id"]) for p in r}
        gone = {p: left(r[p]["run_id"]) for p in r}
        normal = normal_trips(t["P0"], gone["P0"])
        scen = json.loads((ROOT / f"sim/scenarios/tuen-mun/evaluator_IN-26-02615_{label}.json").read_text())
        charged = scen["drivers_leave"]["extra_minutes_outside"]
        row = {"cell": f"{label} {c}", "plans": {}}
        for p in r:
            e = r[p]["metrics"]["total_vehicle_hours_delay"]
            hours, cars = extra_driving(t[p], normal)
            row["plans"][p] = {"delay_E": e, "extra_driving_h": round(hours, 1), "cars_on_a_longer_route": cars,
                               "left_at_ting_kau": len(gone[p]),
                               "corrected": {f"{m:g} min outside": round(e + hours + len(gone[p]) * (m - charged) / 60, 1)
                                             for m in args.outside}}
        out.append(row)
    for row in out:
        print(row["cell"])
        for p, v in row["plans"].items():
            vs = "" if p == "P0" else "  " + " ".join(
                f"{k}: {100 * (v['corrected'][k] / row['plans']['P0']['corrected'][k] - 1):+.1f}%" for k in v["corrected"])
            print(f"  {p}: E {v['delay_E']:7.1f} veh-h, +{v['extra_driving_h']:5.1f} longer drive ({v['cars_on_a_longer_route']} cars), "
                  f"{v['left_at_ting_kau']} left at Ting Kau{vs}")
    (res / "comparison.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
