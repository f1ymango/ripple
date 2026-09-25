import argparse

from src.twin.common import load_json, resolve, run, sumo_tools


def main():
    ap = argparse.ArgumentParser(description="Generate candidate random trips using SUMO's randomTrips.py.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--period", type=float, default=5.0, help="Candidate trip spacing in seconds.")
    args = ap.parse_args()
    cfg = load_json(resolve(args.config))
    out = resolve("sim/work/routes/candidates.rou.xml")
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["py", sumo_tools() / "randomTrips.py", "-n", resolve(cfg["network"]), "-r", out,
         "--begin", cfg.get("begin", 0), "--end", cfg.get("end", 3600), "--period", args.period,
         "--seed", cfg.get("seed", 2026), "--validate"])
    print(f"Candidate trips written: {out}. Use fit_demand.py only after reviewing detector order and route coverage.")


if __name__ == "__main__":
    main()
