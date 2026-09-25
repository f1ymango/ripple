# Aberdeen traffic twin: build and run guide

This is component C of Ripple, the twin: `src/twin/` holds the scripts, `sim/scenarios/` the example configs, and `sim/work/` (git-ignored) everything they generate. Run the commands below from the repository root. It is a starter workflow: add the team's actual detector observations and coordinates before claiming calibration results. No calibration result is claimed until that data is added and the evaluation script is run.

## What the pieces mean

- **Network (`.net.xml`)**: roads, lanes, junctions and legal connections. `netconvert` builds the first draft from OpenStreetMap; OSM is not a ground-truth engineering map, so inspect and edit the result.
- **Route (`.rou.xml`)**: each vehicle's trip and departure time. `randomTrips.py` creates candidate trips; the included fitting script adjusts detector-to-detector route weights against observed counts.
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

Copy `sim/scenarios/detectors.example.json` to `sim/scenarios/detectors.json` and enter the real detector IDs, WGS84 longitude/latitude, observed 5-minute counts, and speeds. One observation row is required per detector per 5-minute interval for the pre-incident calibration hour and incident replay window. Preserve missing values as `null`; do not invent or interpolate observations. The coordinates, detector IDs, times, incident lane list and actual incident duration must come from the team data, not this template. Keep the working `detectors.json` and `scenario.json` local; they are excluded from Git.

Copy `sim/scenarios/scenario.example.json` to `sim/scenarios/scenario.json`. Set incident start, duration, lanes, simulation horizon and route files. Fill `osm_bbox` to cover the complete corridor (including both directions and the western alternative). Coordinate order is west,south,east,north.

Required observed data shape:

```json
{"detector_id":"TD-EXAMPLE","time":"2026-10-01T08:00:00+08:00","count":12,"speed_kmh":31.4}
```

## Step 3 — Download OSM and build the draft network

After checking the bounding box, run:

```powershell
python -m src.twin.build_network --config sim/scenarios/scenario.json
```

This downloads OSM via SUMO's `osmGet.py`, runs `netconvert`, and writes a SUMO network. Inspect it in `sumo-gui` and fix wrong lane counts, junctions, connections and turn bans using a reviewed `netconvert` configuration / plain XML edits. Particularly inspect tunnel approaches, Aberdeen Tunnel, flyovers and the Pok Fu Lam / Shek Pai Wan route. Automated OSM conversion cannot establish that a restriction matches reality. The downloaded map is under `sim/work/osm/`; generated network is under `sim/work/network/`.

## Step 4 — Place matching simulated detectors

```powershell
python -m src.twin.place_detectors --config sim/scenarios/scenario.json --detectors sim/scenarios/detectors.json
```

The script projects each real coordinate to the nearest network edge and writes `sim/work/network/real_detectors.add.xml` with E1 loops and a mapping CSV. Review the map locations and edge direction carefully. A nearest-edge match is only a proposal: approve/correct each edge and position against the road direction and actual detector location before using the outputs.

## Step 5 — Make candidate routes and fit demand

```powershell
python -m src.twin.make_routes --config sim/scenarios/scenario.json
python -m src.twin.fit_demand --config sim/scenarios/scenario.json --detectors sim/scenarios/detectors.json
```

The first command calls SUMO `randomTrips.py`. The fitting command creates candidate origin-destination routes between ordered detectors and estimates nonnegative route weights from pre-incident counts using a transparent iterative least-squares coordinate update. It writes `sim/work/routes/fitted.rou.xml` and a fit summary. This lightweight fitter assumes detector crossing counts are a linear combination of route flows and is not a substitute for SUMO `routeSampler.py` / `dfrouter` when the team's actual detector flow data and full-day route context are available. Check the fit residuals and rerun after correcting routes/network. Do not hide poor fit by changing observations.

## Step 6 — Run the baseline and compare it with reality

```powershell
python -m src.twin.run_scenario --config sim/scenarios/scenario.json --label baseline
python -m src.twin.evaluate --observations sim/scenarios/detectors.json --sim sim/work/results --out sim/work/results/baseline-validation.json
```

The baseline replays the incident with no intervention. Compare simulated and real detector values at the same places and times. The evaluation reports GEH for count bins, percentage below 5, and speed MAPE over available 5-minute bins. Your brief's target is GEH < 5 for at least 85% of count bins. Report the measured result even if it misses. The runner's detector output is aggregated into the observation interval; ensure the configured interval matches the data.

## Step 7 — Run the intervention and sensitivity grid

Put an intervention route file in `sim/scenarios/scenario.json` or specify it with `--plan-routes`. A plan uses the same network, demand, incident and random seed as its baseline counterpart; only the intervention policy differs. Follow the architecture document's definition of driver compliance. The grid runner passes compliance and clearance parameters to the policy hook in `src/twin/policies.py`:

```powershell
python -m src.twin.run_sensitivity --config sim/scenarios/scenario.json
```

The default policy hook is deliberately a no-op until you encode the team's actual rerouting/advice behavior. It will say so in output; do not call those runs intervention results. Once implemented, compare plan vs baseline for benefit and reality vs baseline for credibility. Never describe plan-vs-reality as the algorithm's improvement.

## Incident and model limitations

The incident runner closes the configured edge/lane indices with TraCI and restores them after the configured duration. SUMO uses zero-based lane indices. Confirm edge IDs and lanes in the network before running. The model does not represent stochastic driver behavior, signal timing, queue spillback, lane changing, bus priority or incident response unless you explicitly add and validate those mechanisms. The network, demand fit, detector map, incident timing and compliance assumptions are the main uncertainty sources.

## 25-second validation answer template

“We validate before we claim. We replayed the incident with no intervention and compared simulated detectors against the real detectors at the same locations. [X]% of count bins were within GEH 5, and speed MAPE was [Y]%. The improvement is the validated baseline compared with the plan, and we report outcomes over 30%, 50% and 70% driver compliance.” Replace the brackets only with the evaluation output. If baseline validation is poor, say so and use the simplified network specified by the team's architecture contract.
