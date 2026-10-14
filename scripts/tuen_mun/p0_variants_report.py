"""Tuen Mun P0 variants: what Simulation's predeclared review asks of each one (docs/tuen-mun-p0-simulation-review-2026-10-14.md).

    python scripts/tuen_mun/p0_variants_report.py [--results-dir results/tuen-mun-p0-variants-oct15]
    -> <results-dir>/p0-variants-report.md and .json

Per P0 run (variant x seed), from E's own outputs and TD's archived detector readings:

  validation       E's validation v2 block and whether it is met
  counts           5-minute counts at TDS90024/29/32/33/34 against TD's, where TD's bin has at least 40% archive
                   coverage and 90% valid lane readings; and totals over 17:30-20:30 against TD's
  queue            per detector TDS90020-32: TD's and the model's congested 5-minute bins (under 30 km/h),
                   first and last; mean speed 18:00-18:45 at TDS90024-31, TD against model
  discharge        TDS90033 after the reopening, 18:45-19:00, veh/h
  Sham Tseng exit  vehicles onto the exit slip, and the slip's waiting time
  entry            hours waiting to enter by entry edge; vehicles still waiting at the end
  teleports        by kind and by edge
  ledger           loaded = inserted + waiting; inserted = arrived + still driving; arrived includes the
                   drivers who left at Ting Kau, by exit; Route 3 and Castle Peak Rd flows
"""
import argparse
import collections
import datetime as dt
import glob
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src import validation_targets   # noqa: E402
from src.loaders import detectors     # noqa: E402

WORK = ROOT / "sim/work/evaluator"
HK = dt.timezone(dt.timedelta(hours=8))
BEGIN_MIN = 16 * 60 + 30
COUNT_DETS = ["TDS90024", "TDS90029", "TDS90032", "TDS90033", "TDS90034"]
QUEUE_DETS = [f"TDS900{n}" for n in range(20, 33) if n not in (26,)]
SPEED_DETS = [f"TDS900{n}" for n in range(24, 32)]
EXIT_SLIP = ["158584378", "452269559", "452269553#0"]
CPR_EDGES = {"Sham Tseng exit slip": "158584378", "Castle Peak Rd westbound after Sham Tseng": "389939167#0",
             "Siu Lam on-slip to Tuen Mun Rd": "833525675"}
ROUTE3 = {"1184210823": "Ting Kau Bridge drivers staying on Route 3", "209559418": "Tuen Mun Rd drivers taking the Ting Kau exit"}
TELEPORT = re.compile(r"Teleporting vehicle '[^']+'; waited too long \((\w[\w ]*)\), lane='([^']+)', time=(\d+)")


def clock(second):
    t = BEGIN_MIN + second // 60
    return f"{t // 60:02d}:{t % 60:02d}"


def td_bins():
    start, end = dt.datetime(2026, 4, 15, 16, 30, tzinfo=HK), dt.datetime(2026, 4, 15, 20, 30, tzinfo=HK)
    ids = sorted(set(COUNT_DETS + QUEUE_DETS + SPEED_DETS))
    rows = detectors.load_window(start, end, ids, log=lambda *a: None)
    return {(b["detector_id"], b["bin_start"][11:16]): b
            for b in detectors.bin_window(rows, 5, start=start, end=end, detector_ids=ids)}


def num(v):
    return None if v in (None, "") else float(v)


def model_loops(work):
    n, sv = collections.defaultdict(float), collections.defaultdict(float)
    for f in glob.glob(str(work / "results" / "e1_*.xml")):
        det = Path(f).name[3:].rsplit("_", 1)[0]
        for iv in ET.parse(f).getroot().iter("interval"):
            b = int(float(iv.get("begin"))); k = float(iv.get("nVehContrib")); s = float(iv.get("speed"))
            n[(det, b)] += k
            if k > 0 and s >= 0:
                sv[(det, b)] += k * s * 3.6
    speed = {key: sv[key] / n[key] for key in n if n[key] > 0 and key in sv}
    return n, speed


def edge_data(work):
    out = collections.defaultdict(dict)
    for iv in ET.parse(work / "edges.xml").getroot().iter("interval"):
        b = int(float(iv.get("begin")))
        for e in iv.iter("edge"):
            out[e.get("id")][b] = {k: float(e.get(k, 0)) for k in ("entered", "waitingTime", "left")}
    return out


def one_run(result_path, td):
    r = json.loads(Path(result_path).read_text())
    run_id = r["run_id"]
    rep = json.loads((Path(result_path).parent.parent / "evaluator" / f"{run_id}.report.json").read_text())
    work = WORK / run_id
    met, why = validation_targets.check(r["validation"])
    n, speed = model_loops(work)
    out = {"run_id": run_id, "validation": r["validation"], "validation_met": met, "validation_reason": why,
           "delay_vehicle_hours_E": r["metrics"]["total_vehicle_hours_delay"]}
    # counts
    counts = {}
    for d in COUNT_DETS:
        diffs, tot_m, tot_o = [], 0.0, 0.0
        for b in range(3600, 14400, 300):
            o = td.get((d, clock(b)))
            m = n.get((d, b), 0.0)
            ok = o and o["coverage_pct"] >= 40 and o["lane_completeness_pct"] >= 90 and num(o["count_bin"]) is not None
            if ok:
                diffs.append(m - num(o["count_bin"]))
            if o and num(o["flow_veh_h"]) is not None:
                tot_o += num(o["flow_veh_h"]) / 12
            tot_m += m
        counts[d] = {"model_minus_td_total_1730_2030": round(tot_m - tot_o), "td_total": round(tot_o),
                     "bins_compared": len(diffs), "mean_abs_bin_diff": round(statistics.mean(abs(x) for x in diffs), 1) if diffs else None}
    out["counts"] = counts
    # queue
    queue, both = {}, 0
    for d in QUEUE_DETS:
        ob = [clock(b) for b in range(3600, 12000, 300) if num((td.get((d, clock(b))) or {}).get("speed_kmh")) is not None
              and num(td[(d, clock(b))]["speed_kmh"]) < 30]
        mo = [clock(b) for b in range(3600, 12000, 300) if (d, b) in speed and speed[(d, b)] < 30]
        both += len(set(ob) & set(mo))
        queue[d] = {"td": [ob[0], ob[-1], len(ob)] if ob else None, "model": [mo[0], mo[-1], len(mo)] if mo else None}
    out["queue"] = queue
    out["congested_bins"] = {"td": sum(q["td"][2] for q in queue.values() if q["td"]),
                             "model": sum(q["model"][2] for q in queue.values() if q["model"]), "both": both}
    sp_o = [num(td[(d, clock(b))]["speed_kmh"]) for d in SPEED_DETS for b in range(5400, 8100, 300)
            if num((td.get((d, clock(b))) or {}).get("speed_kmh")) is not None]
    sp_m = [speed[(d, b)] for d in SPEED_DETS for b in range(5400, 8100, 300) if (d, b) in speed]
    out["mean_speed_1800_1845_TDS90024_31"] = {"td": round(statistics.mean(sp_o), 1), "model": round(statistics.mean(sp_m), 1)}
    out["discharge_TDS90033_1845_1900_veh_h"] = {
        "td": [num((td.get(("TDS90033", clock(b))) or {}).get("flow_veh_h")) for b in (8100, 8400, 8700)],
        "model": [round(n.get(("TDS90033", b), 0) * 12) for b in (8100, 8400, 8700)]}
    # edges: Sham Tseng exit, Castle Peak Rd, Route 3
    ed = edge_data(work)
    out["sham_tseng_exit"] = {"vehicles_onto_slip_1730_2030": round(sum(v["entered"] for b, v in ed.get("158584378", {}).items() if 3600 <= b < 14400)),
                              "max_5min_waiting_vehicle_hours_on_slip": round(max((sum(ed.get(e, {}).get(b, {}).get("waitingTime", 0) for e in EXIT_SLIP)
                                                                                  for b in range(1800, 14400, 300)), default=0) / 3600, 2)}
    out["castle_peak_road_entered_1730_2030"] = {name: round(sum(v["entered"] for b, v in ed.get(e, {}).items() if 3600 <= b < 14400))
                                                 for name, e in CPR_EDGES.items()}
    left = json.loads((work / "left-corridor.json").read_text()) if (work / "left-corridor.json").exists() else []
    by_exit = collections.Counter(x.get("edge") or x.get("how") for x in left)
    md, health = rep["measurement_detail"], rep["run_health"]
    out["entry"] = {"hours_waiting_to_enter": md["delay_hours_waiting_to_enter"],
                    "by_entry_edge": md["delay_hours_waiting_to_enter_by_entry_edge"],
                    "vehicles_waiting_at_end": health["vehicles_waiting_to_enter_at_end"]}
    tel = collections.Counter(); where = collections.Counter()
    for line in open(work / "sumo.log", errors="replace"):
        m = TELEPORT.search(line)
        if m:
            tel[m.group(1)] += 1; where[m.group(2).rsplit("_", 1)[0]] += 1
    out["teleports"] = {"by_kind": dict(tel), "by_edge": dict(where.most_common(8)),
                        "wrong_lane_not_at_lane_shut_or_jam": r["validation"].get("wrong_lane_teleports_other")}
    arrived = health["vehicles_inserted"] - health["vehicles_running_at_end"]
    out["ledger"] = {"loaded": health["vehicles_loaded"], "inserted": health["vehicles_inserted"],
                     "waiting_at_end": health["vehicles_waiting_to_enter_at_end"],
                     "arrived": arrived, "still_driving_at_end": health["vehicles_running_at_end"],
                     "left_at_ting_kau": {ROUTE3.get(k, k): v for k, v in by_exit.items()},
                     "balances": health["vehicles_loaded"] == health["vehicles_inserted"] + health["vehicles_waiting_to_enter_at_end"]}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results-dir", default="results/tuen-mun-p0-variants-oct15")
    args = parser.parse_args()
    res = ROOT / args.results_dir
    td = td_bins()
    runs = [one_run(p, td) for p in sorted(glob.glob(str(res / "runs" / "*.json"))) if not p.endswith(".provenance.json")]
    (res / "p0-variants-report.json").write_text(json.dumps(runs, indent=1) + "\n")
    lines = ["# Tuen Mun P0 variants: Simulation's predeclared checks", "",
             f"`scripts/tuen_mun/p0_variants_report.py` on `{args.results_dir}`. "
             "TD: congested 5-minute bins at TDS90020-32 = "
             f"{runs[0]['congested_bins']['td'] if runs else '?'}; mean speed 18:00-18:45 at TDS90024-31 = "
             f"{runs[0]['mean_speed_1800_1845_TDS90024_31']['td'] if runs else '?'} km/h; "
             f"discharge at TDS90033 18:45/18:50/18:55 = {runs[0]['discharge_TDS90033_1845_1900_veh_h']['td'] if runs else '?'} veh/h.", "",
             "| Run | v2 met | GEH | FF err | state | congested bins model / both | mean speed 18:00-18:45 | "
             "discharge 18:45/50/55 | counts 24/29/32/33/34, model - TD | left at Ting Kau | Sham Tseng slip veh / max wait veh-h | "
             "entry wait h | teleports (wrong-lane other) | delay veh-h |",
             "|" + "---|" * 14]
    for x in runs:
        v = x["validation"]
        label = "_".join(x["run_id"].split("_")[5:6])
        lines.append(
            f"| {label} | {'yes' if x['validation_met'] else 'NO'} | {v['geh_under_5_pct']} | {v['speed_mape_free_flow_pct']} | "
            f"{v['congestion_state_agreement_pct']} | {x['congested_bins']['model']} / {x['congested_bins']['both']} | "
            f"{x['mean_speed_1800_1845_TDS90024_31']['model']} | {'/'.join(str(a) for a in x['discharge_TDS90033_1845_1900_veh_h']['model'])} | "
            f"{'/'.join(str(x['counts'][d]['model_minus_td_total_1730_2030']) for d in COUNT_DETS)} | "
            f"{sum(x['ledger']['left_at_ting_kau'].values())} | {x['sham_tseng_exit']['vehicles_onto_slip_1730_2030']} / "
            f"{x['sham_tseng_exit']['max_5min_waiting_vehicle_hours_on_slip']} | {x['entry']['hours_waiting_to_enter']} | "
            f"{sum(x['teleports']['by_kind'].values())} ({x['teleports']['wrong_lane_not_at_lane_shut_or_jam']}) | {x['delay_vehicle_hours_E']} |")
    lines += ["", "Queue per detector (first-last congested bin, count), TD | model, for each run: see the .json."]
    (res / "p0-variants-report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
