"""Tuen Mun twin calibration: an ordinary Wednesday with no incident, against that day's detectors.

    python scripts/tuen_mun/ordinary_run.py --day 2026-04-22 --out sim/work/tuen-mun/ordinary-20260422
    -> <out>/evaluation.json (src/twin/evaluate.py against observations_<day>.json), edges.xml, tripinfo.xml

Same network, loops, vehicle length and SUMO settings as E's replay, without the closure, plans or
drivers' own diversion. Prints the version-2 numbers too (free-flow speed MAPE over bins measured at
30 km/h or more, congestion-state agreement), computed from the same bins. Shares fitted on ordinary days are checked here, never on the incident day.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--day", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--length-m", type=float, default=7.0)
    parser.add_argument("--suffix", default="", help="a demand variant: demand_<day><suffix>.rou.xml (e.g. -sigma05)")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    (out / "results").mkdir(parents=True, exist_ok=True)
    tag = args.day.replace("-", "")
    routes = (ROOT / f"sim/tuen-mun/demand_{tag}{args.suffix}.rou.xml").read_text()
    routes = routes.replace('length="5"', f'length="{args.length_m}"')
    (out / "demand.rou.xml").write_text(routes)
    (out / "detectors.add.xml").write_text((ROOT / "sim/tuen-mun/detectors.add.xml").read_text())
    (out / "edges.add.xml").write_text('<additional><edgeData id="e" period="300" file="edges.xml"/></additional>\n')
    cmd = ["sumo", "-n", str(ROOT / "sim/tuen-mun/network.net.xml"), "-r", "demand.rou.xml",
           "-a", "detectors.add.xml,edges.add.xml", "--begin", "0", "--end", "14400", "--step-length", "1",
           "--seed", str(args.seed), "--tripinfo-output", "tripinfo.xml", "--no-step-log", "true",
           "--log", "sumo.log", "--duration-log.statistics", "true"]
    subprocess.run(cmd, cwd=out, check=True, stdout=subprocess.DEVNULL)
    (out / "config.json").write_text(json.dumps({"observation_start_sim_seconds": 1800}))
    subprocess.run([sys.executable, "-m", "src.twin.evaluate", "--observations",
                    str(ROOT / f"sim/tuen-mun/observations_{tag}.json"), "--sim", str(out / "results"),
                    "--out", str(out / "evaluation.json"), "--config", str(out / "config.json")], cwd=ROOT, check=True)
    ev = json.loads((out / "evaluation.json").read_text())
    free = [b["absolute_percentage_error"] for b in ev["speed_bins"]
            if b["observed_kmh"] >= 30 and b.get("absolute_percentage_error") is not None]
    state = [(b["observed_kmh"] < 30) == (b["simulated_kmh"] < 30) for b in ev["speed_bins"]
             if b.get("simulated_kmh") is not None]
    ev["speed_mape_free_flow_pct"] = round(sum(free) / len(free), 2)
    ev["congestion_state_agreement_pct"] = round(100 * sum(state) / len(state), 2)
    (out / "evaluation.json").write_text(json.dumps(ev, indent=1) + "\n")
    print(args.day, args.suffix or "(default)", {k: ev.get(k) for k in (
        "geh_under_5_percent", "speed_mape_percent", "speed_mape_free_flow_pct", "congestion_state_agreement_pct")},
        file=sys.stderr)


if __name__ == "__main__":
    main()
