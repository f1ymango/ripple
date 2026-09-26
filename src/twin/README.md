# Aberdeen traffic twin: build and run guide

This is component C of Ripple, the twin: `src/twin/` holds the scripts, `sim/` the network and detector loops once they are reviewed (committed, as `docs/03-architecture.md` §2 lays out), `sim/scenarios/` the example configs, and `sim/work/` (git-ignored) the downloads, routes and SUMO output. Run the commands below from the repository root. It is a starter workflow: add the team's actual detector observations and coordinates before claiming calibration results. No calibration result is claimed until that data is added and the evaluation script is run.

## What the pieces mean

- **Network (`.net.xml`)**: roads, lanes, junctions and legal connections. `netconvert` builds the first draft from OpenStreetMap; OSM is not a ground-truth engineering map, so inspect and edit the result.
- **Route (`.rou.xml`)**: each vehicle's trip and departure time. the route builder creates detector-to-detector corridor trips; the fitter adjusts route weights against observed counts and emits rate-based flows across the configured horizon.
- **E1 loop (`.add.xml`)**: a simulated induction loop on an edge. This measures vehicles and speed over a configured interval. Positions are metres along an edge, not latitude/longitude.
- **TraCI**: Python control of a running SUMO simulation. The runner closes selected lanes for the incident duration, then reopens them.
- **GEH and MAPE**: GEH compares count totals; speed MAPE compares 5-minute mean speeds. Keep reality vs baseline separate from plan vs baseline.

## Step 1 — Install and check SUMO

Install SUMO using the official SUMO Windows installer. Open a new PowerShell after installation and make sure `sumo`, `netconvert`, and the SUMO tools directory are available. Set `SUMO_HOME` to the SUMO installation directory if the installer did not do so. Install Python 3.10+ and run these commands from the repository root:

```powershell
python -m pip install -r requirements.txt
python -m src.twin.check_sumo
```

If the check fails, fix the SUMO PATH / `SUMO_HOME` before continuing. The Python packages are listed under component C in the repository root `requirements.txt`; install SUMO itself separately.

## Step 2 — Add the team's inputs

Generate the detector hand-over from the archive cache for the whole replay window; it writes one row per 5-minute slot and preserves unusable counts or unmeasured speeds as `null`:

```powershell
python -m src.loaders.fetch twin-detectors --start 2026-05-15T07:55 --end 2026-05-15T10:35
```

The committed `data/detectors.csv` supplies direction and corridor-leg metadata. `place_detectors` and `make_routes` read those fields from the registry, since the hand-over JSON is focused on observations. Existing hand-reviewed `edge_id` and `position_m` values survive regenerating the file. Keep generated `detectors.json` and `scenario.json` local; they are excluded from Git.

Copy `sim/scenarios/scenario.example.json` to `sim/scenarios/scenario.json`. Set incident start, duration, lanes, simulation horizon and route files. Fill `osm_bbox` to cover the complete corridor (including both directions and the western alternative). Coordinate order is west,south,east,north.

Required observed data shape:

```json
{
  "interval_seconds": 300,
  "detectors": [
    {"id": "TD-EXAMPLE", "lon": 114.17, "lat": 22.25, "edge_id": null, "position_m": null,
     "observations": [{"time": "2026-10-01T08:00:00+08:00", "count": 12, "speed_kmh": 31.4}]}
  ]
}
```

The values above only show the shape; they are not data.

**Moving from the old `simulation_validation/` layout:** move `simulation_validation/work/` to `sim/work/` and `simulation_validation/config/scenario.json` and `detectors.json` to `sim/scenarios/`. In `scenario.json`, change every path that starts with `work/` to start with `sim/work/`, except `network` and `detector_additional`, which become `sim/aberdeen.net.xml` and `sim/detectors.add.xml`. Paths now resolve from the repository root.

## Step 3 — Download OSM and build the draft network

After checking the bounding box, run:

```powershell
python -m src.twin.build_network --config sim/scenarios/scenario.json
```

This downloads OSM via SUMO's `osmGet.py`, runs `netconvert` with left-hand traffic enabled for Hong Kong, and writes a SUMO network. Inspect it in `sumo-gui` and fix wrong lane counts, junctions, connections and turn bans using a reviewed `netconvert` configuration / plain XML edits. Particularly inspect tunnel approaches, Aberdeen Tunnel, flyovers and the Pok Fu Lam / Shek Pai Wan route. Automated OSM conversion cannot establish that a restriction matches reality. The downloaded map is under `sim/work/osm/`; the network is written to `sim/aberdeen.net.xml`. Commit it once it has been inspected and corrected, so the Evaluator and teammates use the same network.

## Step 4 — Place matching simulated detectors

```powershell
python -m src.twin.place_detectors --config sim/scenarios/scenario.json --detectors sim/scenarios/detectors.json
```

The script matches each real coordinate to a nearby edge whose direction agrees with the detector registry, then writes one E1 loop per lane and a mapping CSV. If no edge meets the bearing threshold, it stops and asks for a map-reviewed `edge_id` / `position_m`; it does not silently select the opposite carriageway. Review all proposed positions and lane indices on a map before using them.

When the hand-over contains a replay window, the mapper reads lane labels from the matching local raw-cache periods. An OSM street-name alias can identify a detector road only when that window's measured lane count also agrees with the candidate; lane count can break ties between nearby, equally named edges. It does not change OSM lanes or detector readings. After placing detectors, generate the offline source and route audit:

```powershell
python -m src.twin.audit_network --config sim/scenarios/scenario.json --detectors sim/scenarios/detectors.json --out results/twin/osm-network-audit.json
```

The audit reads only local files. If the configured scenario names `detector_overrides`, the override file must carry SHA-256 hashes for the exact network and committed detector registry. The matcher rejects it if either source changes; re-review the locations after every network rebuild. Lane-count conflicts and missing raw snapshots remain visible in the audit. A passing map audit does not establish traffic calibration or prove that SUMO teleport warnings are fixed.

## Step 5 — Make candidate routes and fit demand

```powershell
python -m src.twin.make_routes --config sim/scenarios/scenario.json
python -m src.twin.fit_demand --config sim/scenarios/scenario.json --detectors sim/scenarios/detectors.json
```

The first command creates directed, detector-to-detector candidate trips within each configured corridor leg. The fitting command estimates nonnegative route weights from pre-incident counts and writes one rate-based `<flow>` per route across the configured simulation horizon. It writes `sim/work/routes/fitted.rou.xml` and a fit summary. This lightweight fitter assumes detector crossing counts are a linear combination of route flows and is not a substitute for SUMO `routeSampler.py` / `dfrouter` when the team's actual detector flow data and full-day route context are available. Check the fit residuals and rerun after correcting routes/network. Do not hide poor fit by changing observations.

## Step 6 — Run the baseline and compare it with reality

```powershell
python -m src.twin.run_scenario --config sim/scenarios/scenario.json --label baseline
python -m src.twin.evaluate --observations sim/scenarios/detectors.json --sim sim/work/results --config sim/scenarios/scenario.json --out results/twin/baseline-validation.json
```

The baseline replays the incident with no intervention and stops at the configured `end` time (or `--max-seconds`) even when vehicles remain. `max_depart_delay` limits vehicles unable to enter; inspect the run summary and SUMO duration statistics because this can discard demand. The run saves sampled FCD trajectories and trip information. Evaluation matches observations by timestamp plus `observation_start_sim_seconds`, aggregates all lane loops per detector, sums counts, computes volume-weighted speed and scores observed zero-count bins separately even when speed is null. Configure the horizon to include warm-up and every observation interval. The target is GEH < 5 for at least 85% of count bins; report the measured result, including any missing comparisons.

The evaluator reads SUMO E1's `speed` value in m/s (`-1` means no vehicle was collected) and computes count and speed scores independently, so an absent count does not discard a usable speed observation. It also records missing detector files and unmatched observation intervals; `meets_85_percent_target` stays false when any count observation lacks a comparison. See [SUMO's E1 output fields](https://sumo.dlr.de/userdoc/Simulation/Output/Induction_Loops_Detectors_%28E1%29.html).

## Step 7 — Run the intervention and sensitivity grid

Set `plan_routes` in `sim/scenarios/scenario.json` to an intervention route file, or pass it with `--plan-routes`. A plan uses the same network, demand, incident and random seed as its baseline counterpart; only the intervention policy differs. Follow the architecture document's definition of driver compliance. The grid runner passes compliance and clearance parameters to the policy hook in `src/twin/policies.py`:

```powershell
python -m src.twin.run_sensitivity --config sim/scenarios/scenario.json
```

The default policy hook is deliberately a no-op until you encode the team's actual rerouting/advice behavior. It will say so in output; do not call those runs intervention results. Once implemented, compare plan vs baseline for benefit and reality vs baseline for credibility. Never describe plan-vs-reality as the algorithm's improvement.

## Incident and model limitations

The incident runner closes the configured edge/lane indices with TraCI and restores them after the configured duration. SUMO uses zero-based lane indices. Confirm edge IDs and lanes in the network before running. The model does not represent stochastic driver behavior, signal timing, queue spillback, lane changing, bus priority or incident response unless you explicitly add and validate those mechanisms. The network, demand fit, detector map, incident timing and compliance assumptions are the main uncertainty sources.

## 25-second validation answer template

“We validate before we claim. We replayed the incident with no intervention and compared simulated detectors against the real detectors at the same locations. [X]% of count bins were within GEH 5, and speed MAPE was [Y]%. The improvement is the validated baseline compared with the plan, and we report outcomes over 30%, 50% and 70% driver compliance.” Replace the brackets only with the evaluation output. If baseline validation is poor, say so and use the simplified network specified by the team's architecture contract.
