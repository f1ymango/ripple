"""Package the two demo incidents for the console: each one's main cell, plans, ranking and verdict (Data, 16 Oct cut).

    python scripts/demo_pack.py
    -> results/demo-oct16/<incident>/runs/       the main cell's P0, P1 and P2 results with provenance sidecars
                                    evaluator/   their E run reports
                                    plans/       the plan set as D's validator returned it, with generation inputs
                                    rankings/    the plan set's ranking over its grid (results/rankings/)
                                    verdict.json what the console concludes for that cell (src/console/recommendation.py)

Files are copied unchanged from where E and the ranking tool wrote them; nothing is computed here except the
console's own verdict, which is checked against the expected one. To show one incident in the console:

    RIPPLE_RESULTS_DIR=results/demo-oct16/<incident>/runs RIPPLE_PLANS_DIR=results/demo-oct16/<incident>/plans \\
        streamlit run src/console/app.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.console import recommendation   # noqa: E402

OUT = ROOT / "results/demo-oct16"
INCIDENTS = {
    "aberdeen": {
        "incident_id": "IN-26-03365", "plans": "data/generated-plans/IN-26-03365-lead-draft-20261013-b",
        "plan_set": "lead-draft-20261013-b", "results": "results/evaluator-lead-draft-20261013-b",
        "cell": "2026-05-15_ABD_{plan}_c50_t66_replay-v3-1_lead-draft-20261013-b",
        "ranking": "results/rankings/lead-draft-20261013-b.json", "expect": None,
        "why": "the observed-incident case: the ranking ties P0 and P2 over 33 cells, so Ripple refuses to recommend"},
    "tuen-mun": {
        "incident_id": "IN-26-02615", "plans": "data/generated-plans/IN-26-02615-lead-capacity-oct15",
        "plan_set": "lead-capacity-oct15", "results": "results/tuen-mun-lead-grid-oct15-p0x-merge-at-site",
        "cell": "2026-04-15_TMR_{plan}_c50_t59_p0x-merge-at-site-s2029_lead-capacity-oct15",
        "ranking": "results/rankings/lead-capacity-oct15-p0x-merge-at-site.json", "expect": "P2",
        "why": "the modelled case: the team's ranking puts the Lead's frozen 11% P2 before P0 and P1 over 18 cells"},
}


def pack(name, spec):
    out = OUT / name
    if out.exists():
        raise FileExistsError(f"{out} exists; a demo pack is written once")
    for sub in ("runs", "evaluator", "plans", "rankings"):
        (out / sub).mkdir(parents=True)
    src = ROOT / spec["results"]
    for plan in ("P0", "P1", "P2"):
        run = spec["cell"].format(plan=plan)
        for suffix in (".json", ".provenance.json"):
            shutil.copy2(src / "runs" / f"{run}{suffix}", out / "runs")
        shutil.copy2(src / "evaluator" / f"{run}.report.json", out / "evaluator")
        shutil.copy2(ROOT / spec["plans"] / f"{plan}.json", out / "plans")
    shutil.copy2(ROOT / spec["plans"] / "generation-inputs.json", out / "plans")
    shutil.copy2(ROOT / spec["ranking"], out / "rankings" / f"{spec['plan_set']}.json")
    results, _ = recommendation.read_objects(out / "runs")
    (key,) = recommendation.scenarios_for(results, spec["incident_id"])
    comparison, reason = recommendation.load_comparison(out / "runs", out / "plans", spec["incident_id"], key)
    winner = comparison["winner"]["plan_id"] if comparison else None
    if winner != spec["expect"]:
        raise ValueError(f"{name}: the console gives {winner or 'no recommendation'} ({reason}), not {spec['expect']}")
    verdict = {"incident_id": spec["incident_id"], "plan_set": spec["plan_set"], "why_this_case": spec["why"],
               "cell": {"compliance": key[0], "clearance_min": key[1], "seed": key[2]},
               "copied_from": {"results": spec["results"], "plans": spec["plans"], "ranking": spec["ranking"]},
               "console_recommends": winner, "console_reason_if_none": reason or None,
               "simulated_total_delay_vehicle_hours": {pid: r["metrics"]["total_vehicle_hours_delay"]
                                                        for pid, r in sorted(recommendation.load_comparison(
                                                            out / "runs", out / "plans", spec["incident_id"], key)[0]["runs"].items())}
               if comparison else {r["plan_id"]: r["metrics"]["total_vehicle_hours_delay"] for r in results},
               "generated_by": "python scripts/demo_pack.py"}
    (out / "verdict.json").write_text(json.dumps(verdict, indent=1) + "\n")
    print(name, "->", winner or f"no recommendation: {reason}", file=sys.stderr)


def main():
    for name, spec in INCIDENTS.items():
        pack(name, spec)


if __name__ == "__main__":
    main()
