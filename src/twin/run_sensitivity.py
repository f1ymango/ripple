import argparse
import subprocess
import sys

from src.twin.common import ROOT, load_json, resolve


def main():
    ap = argparse.ArgumentParser(description="Run the 3x3 compliance and clearance sensitivity grid.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--plan-routes")
    args = ap.parse_args()
    cfg = load_json(resolve(args.config))
    plan = args.plan_routes or cfg.get("plan_routes")
    if not plan:
        raise SystemExit("Set plan_routes in scenario.json or pass --plan-routes to the intervention route file.")
    for compliance in (0.3, 0.5, 0.7):
        for clearance in (30, 60, 90):
            label = f"plan_c{int(compliance*100)}_t{clearance}"
            subprocess.run([sys.executable, "-m", "src.twin.run_scenario", "--config", args.config,
                            "--label", label, "--plan-routes", plan, "--compliance", str(compliance),
                            "--clearance", str(clearance)], check=True, cwd=ROOT)


if __name__ == "__main__": main()
