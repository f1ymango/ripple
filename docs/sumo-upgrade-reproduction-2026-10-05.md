# SUMO upgrade reproduction and assumption handout

**For the 5 October model review.** This handout reproduces the reporter's
15 May no-closure case, shows which assumptions changed, and names the evidence
still needed before an incident or plan comparison can be trusted. The source
is `SUMO_Upgrade_Report.docx` supplied to Simulation and Data's merged
[upgrade report](https://github.com/f1ymango/ripple/blob/4875a85/docs/sumo-flow-balance-2026-10-04.md).
The supplied Word report's SHA-256 is
`80ec6ef9b95d10cbb5a6c970834d6378968d4833b1e5f1584a7a7e0d85260252`;
it is a review source, not a simulation input or a committed artifact.
The exact saved results are in the repository. The original SUMO inputs are in
Simulation's provisional archive on `sim/e1-evaluation-correctness`.

## Case and comparable scores

**Observed hour:** 15 May 2026, 07:55–08:55 HKT. All runs below have no
closure and seed 2026; counts use the same 242 eligible detector/time bins
(40% archive coverage, 90% valid lane readings). The observation export hash
is `a1d842a25ff872091b47fb3e7bcad566fe9932af0bc5452be3f79fc1462a4605`.
Speed availability differs by one bin in the original run. All count-setting
and scoring roles must be shown; the original fitter used the scored hour's
counts, while Data's upgrade uses the demo day's four first-detector counts
and ordinary days for internal joins/exits and speeds.

| Run | GEH under 5, five-minute bins | Speed MAPE | Waiting outside | Teleports |
|---|---:|---:|---:|---:|
| Original, `results/twin/oct02-flow-trace.json` on the Simulation branch | 162/242, 66.94% | 41.42%, 298 bins | 2,390/17,922, 13.34% | 53 (41 jam, 7 yield, 5 wrong-lane) |
| Simulation's boundary-only experiment, `results/twin/oct03-boundaries.json` | 178/242, 73.55% | 45.98%, 299 bins | 2,016/13,622, 14.80% | 14, all wrong-lane |
| Data's upgrade, `results/twin/oct04-flow-balance.json` on main | 234/242, 96.69% (published rounded 96.7%) | 15.7%, 299 bins | 238/16,601, 1.43% | 0 |
| Data's quarter-hour speed refresh, `results/twin/oct04-flow-balance-refreshed.json` | 236/242, 97.52% | 13.2%, 299 bins | 335/16,601, 2.02% | 0 |

The four rows are **not** a one-variable experiment. The Data upgrade changes
demand, network connections, speed control, driver settings and warm-up. The
refresh additionally uses each detector's own preceding-quarter-hour speed;
it is a time-forward forecast check, not ordinary-day-only calibration.
Neither upgrade row validates the crash, queue recovery or diversion benefit.

## What each model assumes

| Decision | Original Simulation packet | Boundary-only experiment | Data upgrade on main | Evidence or review needed |
|---|---|---|---|---|
| Vehicle origins and exits | Candidate routes begin/end on detector edges; fitted to all available counts in the hour | Existing passenger-legal branch roads selected where May net change exceeds its sampling margin; weights fitted to the same hour's counts | Four first detectors set that day's entry demand; ordinary Fridays set net joins/exits, assigned to mapped ramps by lane count | Net detector differences measure aggregate change, **not** each ramp's turning volume or OD split. Record every inferred allocation. |
| Missing ramp or shared detector edge | Identical edge crossing signatures can hide two loop positions | Position-aware crossing; an unresolved AID01106/07 increase remains where the network has no intervening junction | Builder may inject a measured join on the main line when no mapped ramp exists; cuts edge `1198101443` at 40 m for separate speed signs | Do not present a main-line entry as an observed physical access road. Check mapping and OSM/TD road sources. |
| Road map | Provisional OSM network, SHA `e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e` | Same network and detector loops | Copy made by the committed `.con.xml`/`.edg.xml` patches; saved patched-network SHA `9e23e7de17a5a2e351a59cb6e21031136854c36da9036589694a240597d724cb` | Patch adds/moves toll-plaza lane connections. Cached OSM has `motor_vehicle:lanes=no|yes|yes|yes` at `1198101424`; physical access and turn movements need review. The speed-sign edge cut is a model segmentation, not new road geometry. |
| Speeds | Network limits and SUMO behaviour; no unsupported global 60 km/h cap | Same | Variable signs impose ordinary-day, detector-derived speed for every 15-minute stretch; refresh uses the current day's earlier 15 minutes | Imposed speed can explain MAPE but cannot prove endogenous queues or recovery. Do not call the 15.2% direct input-vs-observation difference an error floor. |
| Driver variation | SUMO default for vehicle type, with `departSpeed="desired"` | Same | `speedFactor=1`, `speedDev=0.05`, `sigma=0`, `departSpeed="max"` | These are modelling choices; detector mean speed does not uniquely measure the driver distribution. |
| Warm-up and horizon | 07:40–07:55 warm-up; 4,500 s to 08:55 | Same | 07:25–07:55 warm-up; 5,400 s to 08:55 | Different warm-up can change inserted/running vehicles and first scored bins. Hold it fixed for any causal one-change test. |
| Fit versus assessment | The scored hour's counts set the route weights | Same, with different physical routes | Four first detectors set that day's demand; 21 others assess count propagation, but ordinary-day profiles and map rules are still fitted choices | “Assessment only” is a useful split, not independent validation of incident effects or all model assumptions. |

Data's saved build notes also disclose an entry road at `244383597` forced to
the exit it leads to, a +201 veh/h western join placed on the main line because
no ramp is mapped, and two small changes left out. The reporter's wording that
the upgrade tells SUMO *only measured things* and that *two map faults were
repaired* is therefore too definite. The paths and aggregate counts are sourced;
the allocation, connection patch and driver settings still require judgement.

## Reproduce the original and upgrade on Windows

Run from a clean checkout of the Simulation branch with Python requirements
installed and SUMO 1.27.1 on `PATH`. Use fresh work/output names. The archive is
**provisional** and should be extracted into a separate checkout, never over a
reviewed network. The saved manifests list hashes. These commands make no
incident closure and use bounded simulation runs.

```powershell
git fetch origin
git switch sim/e1-evaluation-correctness
git worktree add --detach sim/work/repro-main origin/main
Expand-Archive -LiteralPath results/twin/oct04-provisional-replay-inputs.zip -DestinationPath sim/work/repro-main

# Recheck Simulation's original 07:40–08:55 run from this branch.
& .venv\Scripts\python.exe -m src.twin.diagnose_preincident `
  --config sim/work/oct02-calibration/network-speed.json `
  --observations sim/scenarios/detectors.json `
  --work sim/work/repro-original-new `
  --out results/twin/repro-original-new.json `
  --timeout 180 --trace-flow

# Build Data's upgraded model inside the isolated main worktree.
Set-Location sim/work/repro-main
$ripplePython = (Resolve-Path ..\..\..\.venv\Scripts\python.exe).Path
netconvert -s sim/work/aberdeen.net.xml `
  -x sim/scenarios/aberdeen-flow-balance.con.xml `
  -e sim/scenarios/aberdeen-flow-balance.edg.xml `
  -o sim/work/aberdeen.flow-balance.net.xml `
  --lefthand true --output.street-names true
& $ripplePython -m src.twin.flow_balance_demand `
  --inputs sim/scenarios/twin-inputs_20260515.json `
  --network sim/work/aberdeen.flow-balance.net.xml `
  --out sim/work/repro-flow-balance-new
& $ripplePython -m src.twin.run_flow_balance `
  --inputs-dir sim/work/repro-flow-balance-new `
  --network sim/work/aberdeen.flow-balance.net.xml `
  --loops sim/work/may-diagnostic/detectors.add.xml `
  --observations sim/scenarios/detectors.json `
  --out results/twin/repro-flow-balance-new.json `
  --seed 2026 --timeout 180
```

`sim/scenarios/twin-inputs_20260515.json` is committed on main; it names the
four ordinary Fridays (8 May, 24 Apr, 17 Apr, 10 Apr), source detector roles,
15-minute entry steps, pair changes and speed profiles. The raw TD cache is
needed to **regenerate** this handover through `python -m src.loaders.fetch
twin-inputs`; it is not needed to replay the committed handover. Keep the exact
network, loop, route and observation hashes printed in each report. A differing
network hash requires review before comparing scores, even if the run finishes.

### Check the hourly-equivalent result

Return to the Simulation worktree and score the two saved reports on the
identical eligible pairs:

```powershell
Set-Location ..\..\..
& .venv\Scripts\python.exe -m src.twin.audit_hourly_geh `
  --reference results/twin/oct02-flow-trace.json `
  --candidate sim/work/repro-main/results/twin/oct04-flow-balance.json `
  --out results/twin/repro-hourly-geh-new.json
```

The published upgrade file on main gives **19/25** detectors with hourly-
equivalent GEH < 5; the original gives **11/25**. The script sums each
detector's eligible five-minute bins, multiplies both observed and simulated
sums by `12 / eligible_bins`, and applies GEH to those hourly equivalents. The
archive has gaps, so this is **not a directly observed complete-hour count**.
Using unscaled sums gives a different result (23/25 and 12/25); always name
the method. The [saved audit](../results/twin/oct05-hourly-geh.json) records
every detector's bin count and both scores. The five-minute headline remains
the team's agreed 242-bin measure; the hourly-equivalent result is a necessary
sensitivity check, not a replacement contract.

## What can and cannot be presented

- **Supported now:** saved no-closure scores and source hashes on Aberdeen;
  one upgraded run's 21 internal detectors score 96.6% GEH over 205 bins.
- **Not yet established:** a reviewed tunnel lane/access patch, observed OD
  splits, physical incident onset/lane choice, queue formation/spillback,
  recovery, rerouting compliance, and matching P0/P1/P2 results with original
  provenance sidecars. The upgrade's 15.7% speed MAPE remains slightly above
  the team's approximate 15% target. Its ramp still has 238 vehicles waiting.
- **Other roads:** the Word report quotes Kwun Tong Bypass and Island Eastern
  Corridor scores, and explicitly says the setup scripts and run files are not
  in the repository. Do not promote those numbers to reproducible project
  evidence until Data commits exact networks, observations, code, commands,
  source hashes, scored-bin sets and results. Island Eastern Corridor also
  required a road-name placement rule after its first trial, and reports large
  entry backlogs; “no hand tuning” needs that qualification.

The decision for 5 October is whether these assumptions support a limited
no-closure SUMO baseline and what incident checks remain. Do not use the count
score alone to validate a crash or rank plans. Data owns the fallback/E, Lead
owns the model decision and main merge, and Simulation owns this SUMO review.

**Local verification on 5 October:** the saved main results and hourly scores
were read and recomputed from committed count rows. A new SUMO replay could not
be completed here: both installed Windows executables, `sumo.exe` and
`netconvert.exe`, exited before printing a version with process code
`0xC0E90002`, including an attempted unsandboxed version check. The commands
above are specified for a working SUMO installation; the saved 4 October Data
run was made on Linux with SUMO 1.27.1, and its Windows execution is still
unverified.
