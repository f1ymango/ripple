# Source-backed boundary experiment — reviewed 4 October

## Result: better counts, not an acceptable baseline

The bounded no-closure experiment completed all 4,500 simulation seconds on
3 October. Same seed 2026, network, E1 loops, May 15 observations, 07:55–08:55
scoring window, 15-minute warm-up, 40%/90% count filtering and network-derived
speed limits. Only route construction and the consequent count refit changed.
No road geometry, connection, signal, observed value or teleport setting changed.

| Measure | Instrumented reference | Boundary candidates |
|---|---:|---:|
| GEH < 5 | 162/242, 66.94% | 178/242, **73.55%** |
| Speed MAPE, common 298 bins | 41.42% | 45.42% |
| Speed MAPE, all scored bins | 41.42%, 298 | 45.98%, 299 |
| Eligible but unscored speed bins | 1 | 0 |
| Missing detectors / unmatched count bins | 0 / 0 | 0 / 0 |
| Loaded / inserted | 17,922 / 15,532 | 13,622 / 11,606 |
| Waiting / share of loaded | 2,390 / 13.34% | 2,016 / **14.80%** |
| Still running | 1,547 | 1,837 |
| Teleports: jam / yield / wrong-lane | 41 / 7 / 5 | 0 / 0 / **14** |
| Diagnostic wall seconds / limit | 47.45 / 180 | 79.89 / 180 |

Evidence: [comparison with per-detector scores](../results/twin/oct03-boundaries-comparison.json),
[full run](../results/twin/oct03-boundaries.json),
[delivery reconciliation](../results/twin/oct03-boundaries-delivery.json).
The diagnostic wall timer includes process startup; SUMO's own duration differs.

**Do not adopt this as a calibrated baseline.** It misses both the 80% recovery
goal and 85% formal count target, worsens speed error, has a larger waiting
fraction and more wrong-lane teleports. Lower total teleports alone is not a
physical-flow pass. This remains an opt-in experiment, not the default generator.

## What was implemented and why

`boundary_routes` reads Data's measured net-flow evidence from main (`fc413a5`,
`results/data/flow-balance_20260515-0755_0855.json`). It selects stretches where
the reported May 15 net change exceeds its sampling margin. It follows only
existing passenger-legal connections, extends unambiguous branches to their
first junction, rejects cyclic/spine-bypass branches, and creates connected
entry-to-exit paths along each directed corridor. It emits 48 candidates and
an audit of every selected boundary and unresolved net change.

It does **not** allocate Data's net difference to invented side-road volumes.
The unchanged count targets determine nonnegative route weights. These are
inferred, non-unique OD weights, not measured OD flows. The new route set joins
trips that the old detector-to-detector representation split apart, so total
generated vehicles change; total trip count is not conserved between different
OD representations. This is disclosed, not an arbitrary percentage demand cut.
Some targets cannot be fitted exactly on the available geometry; the bundled
fit summary preserves their residuals. No target or scored bin is removed.

`route_crossings` checks start/end positions. Starting downstream of a loop
does not count as crossing it, and a terminal vehicle must clear the loop with
its rear for E1 `nVehContrib`. Unsupported random/free endpoints and repeated
edges fail explicitly. The fitter preserves candidate endpoint positions and
types. Legacy mappings without positions retain edge-only behaviour but are
listed in the fit report; the real experiment uses positions throughout.
See [SUMO E1 semantics](https://sumo.dlr.de/docs/Simulation/Output/Induction_Loops_Detectors_(E1).html).

`fit_demand --no-closure` preserves the complete fitted rate without the old
incident-edge origin suspension. The 15-minute warm-up starts from an empty
network at the same fitted hourly rate; it creates no fabricated initial queue.
This is an explicit extrapolation, not measured 07:40–07:55 demand. Fitting and
scoring reuse the same hour and all available count detectors: **not independent
validation**.

## Why the remaining failures persist

- The previous AID01103 origin backlog disappears, but the real ramp feeding
  AID01109 now has 984 undeparted vehicles at origin `26434907`. This exposes a
  physical merge/arrival limitation rather than solving it through extra trips
  injected at the downstream detector.
- AID01214 improves to 9/10 passing bins, but an approach route still requires
  a difficult lane change and causes all 14 wrong-lane teleports. Existing
  edge connectivity does not establish a feasible approach-to-exit OD split.
- AID01106/07 share one edge with no intervening junction. Their measured
  increase cannot be assigned to a new access road on this network. The route
  audit also leaves the western TDSSPWR10003-to-TDSAPR10001 increase unresolved.
- Remaining count misses concentrate at AID01109, AID01221, AID01219 and
  AID01222. The comparison includes every detector's pass counts, observed and
  simulated totals, and speed error contribution.
- Speed error is dominated by AID01106, TDSSPWR20001, AID01216 and AID01110.
  This does not justify globally capping vehicle speed. Placement, recurring
  queues, entry delivery and real signal evidence remain necessary.

## Reproduction

Use the simulation branch with Python 3.14.3 and SUMO 1.27.1. Extract
[the source-checked archive](../results/twin/oct04-boundary-experiment-inputs.zip)
at the root of a fresh checkout. The adjacent manifest includes hashes. It
contains the provisional network, original OSM, observed export, loops/mapping,
exact candidates/fitted routes/config, Data net-flow evidence, fit summary and
boundary audit. It is not a reviewed network release.

```powershell
python -m src.twin.diagnose_preincident --config sim/work/oct03-boundaries/scenario.json --observations sim/scenarios/detectors.json --work sim/work/boundary-review-new --out results/twin/boundary-review-new.json --timeout 180 --trace-flow
python -m src.twin.audit_route_delivery --config sim/work/oct03-boundaries/scenario.json --diagnostic results/twin/boundary-review-new.json --out results/twin/boundary-review-new-delivery.json
python -m src.twin.compare_calibration --reference results/twin/oct02-flow-trace.json --candidate results/twin/boundary-review-new.json --change "Existing entry/exit routes and consequent count refit" --out results/twin/boundary-review-new-comparison.json
```

To regenerate candidates and demand instead of replaying saved inputs:

```powershell
python -m src.twin.boundary_routes --config sim/work/oct02-calibration/network-speed.json --flow-evidence sim/work/oct03-evidence/flow-balance_20260515-0755_0855.json --out sim/work/boundary-build-new
python -m src.twin.fit_demand --config sim/work/boundary-build-new/scenario.json --detectors sim/scenarios/detectors.json --no-closure
```

The build command also needs the original reference archive extracted into the
fresh checkout, since it deliberately preserves that reference's vehicle type.
Use fresh output names. No incident closure is applied by this diagnostic.

Checks: **51 Component C tests passed**, including endpoint crossing, real
connection selection, cycle rejection, source-margin selection, endpoint
preservation and no-closure demand conservation. Archive integrity was checked.
An independent fresh-checkout replay has not been performed.

## Next decision

Data's subsequently merged 4 October pipeline reports much stronger counts but
changes network/OD/speed assumptions. [The Simulation review and Visuals handoff](simulation-handoff-2026-10-04.md)
explain why its reported 96.7% cannot yet be called accepted incident validation.
Prioritise that review for 5 October; do not spend Week 3 on open-ended tuning of
this 73.55% experiment. Keep the fallback subject to its own evidence and narrow
the demonstration if neither model can support incident and plan-effect claims.
