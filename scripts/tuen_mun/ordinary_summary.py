"""Tuen Mun twin: the version-2 numbers of ordinary-day runs (scripts/tuen_mun/ordinary_run.py), side by side.

    python scripts/tuen_mun/ordinary_summary.py --out results/<folder>/ordinary-days.json \
        sim/work/tuen-mun/<run> [sim/work/tuen-mun/<run> ...]

Each run folder holds the evaluation.json ordinary_run.py wrote. Nothing is fitted here.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.validation_targets import COUNT_TARGET, SPEED_TARGET, STATE_TARGET   # noqa: E402

KEYS = ("geh_under_5_percent", "speed_mape_free_flow_pct", "congestion_state_agreement_pct", "speed_mape_percent")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("runs", nargs="+")
    args = parser.parse_args()
    rows = []
    for run in args.runs:
        ev = json.loads((ROOT / run / "evaluation.json").read_text())
        row = {"run": run, **{k: ev[k] for k in KEYS}}
        row["meets_version_2"] = (row["geh_under_5_percent"] >= COUNT_TARGET and row["speed_mape_free_flow_pct"] <= SPEED_TARGET
                                  and row["congestion_state_agreement_pct"] >= STATE_TARGET)
        rows.append(row)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"generated_by": "python scripts/tuen_mun/ordinary_summary.py", "runs": rows}, indent=1) + "\n")
    for r in rows:
        print(r["run"], {k: round(r[k], 2) for k in KEYS}, r["meets_version_2"], file=sys.stderr)


if __name__ == "__main__":
    main()
