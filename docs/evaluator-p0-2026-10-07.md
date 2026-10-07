# E — first provenance-bound P0 for IN-26-03365 (7 October)

Prepared by Data. **The run is not accurate enough to compare plans against.**
It exists to show that E, the result contract and the provenance sidecar work
end to end on the real inputs.

## Is it accurate enough? No

| Check, against the targets in [03-architecture.md](03-architecture.md) §4 | Target | This run |
|---|---|---|
| Count bins with GEH < 5 (607 bins, 07:55–10:35) | at least 85% | **87.14%**, met |
| Speed error, MAPE (790 bins) | at most 15% | **47.34%**, missed |

The count score passes only because of the hour before the closure:

| Phase | GEH < 5 | Speed MAPE |
|---|---|---|
| Before the closure, 07:55–08:55 | 96.28% of 242 | 39.58% of 299 |
| During the assumed closure, 08:55–10:02 | 80.90% of 267 | 60.31% of 341 |
| After reopening, 10:02–10:35 | 81.63% of 98 | 33.27% of 150 |

The run's health is also poor: 840 of 33,505 vehicles (2.5%) never entered,
all of them ramp flow `f22`, and there were 72 teleports, 9 of them
wrong-lane. Data's own proposed rule
([notes](notes-from-data.md), 30 Sep, item 11) would not count a run with
over 1% waiting or any wrong-lane teleport.

F's gate refuses this baseline, as it should. Nothing here contradicts
Simulation's [P0 diagnostic](https://github.com/f1ymango/ripple/blob/4ec5afe/docs/p0-diagnostic-2026-10-07.md):
E ran the same inputs and got the same vehicles (33,505 loaded, 32,665
entered, 840 waiting, 72 teleports) and the same score to every digit
(87.1499% and 47.3320%).

## What was run

- **Plan:** [P0](../data/generated-plans/IN-26-03365-p0-only/P0.json), written
  by `src.evaluator.do_nothing_plan` from D's validator with no model call.
  D's own P0 will replace it, and P0 must then be run again.
- **Context:** [first-report context](../data/plan-context/IN-26-03365_first-report.md),
  marked reviewed by Data today with its judgement calls listed.
- **Scenario:** [evaluator_IN-26-03365.json](../sim/scenarios/evaluator_IN-26-03365.json).
  Simulation's 7 Oct packet unchanged; slow lane closed at 08:55, both lanes
  at 09:36, reopened at 10:02. These are the assumptions agreed for the
  diagnostic, not observed facts.
- **Command and output:** see [src/evaluator/README.md](../src/evaluator/README.md).
  Run three times on Linux (Python 3.13.16, SUMO 1.27.1); the result file was
  byte-identical each time. Not run on Windows.

## The result

[results/runs/2026-05-15_ABD_P0_c50_t67_assumed-0855-0936.json](../results/runs/2026-05-15_ABD_P0_c50_t67_assumed-0855-0936.json),
with its [sidecar](../results/runs/2026-05-15_ABD_P0_c50_t67_assumed-0855-0936.provenance.json)
and [run report](../results/evaluator/2026-05-15_ABD_P0_c50_t67_assumed-0855-0936.report.json).

| Metric | Value | Read it as |
|---|---|---|
| Total delay | 2,583.9 vehicle-hours | 1,149.4 in the network; 1,434.5 waiting to enter, of which 1,388.4 is ramp flow `f22` |
| Longest queue behind the closure | 1,961 m | At least: the path is 1,971 m and the queue reached the network entry |
| Corridor travel time, 95th percentile | 30.4 min | Aberdeen Praya Road entry to Canal Road Flyover; 102 of 2,284 vehicles had not finished |
| Emergency route travel time | 2.8 min | Placeholder: candidate route, 8 of 40 edges carry modelled traffic |
| CO₂ | 17,169 kg | One default emission class for every vehicle |
| Delay on residential streets | 0.3% | The demand barely uses them |
| Vehicles completed | 26,148 of 28,023 in scope | 1,035 still driving, 840 never entered |

Do not quote these as incident impacts. They describe a model run that does
not yet match the morning.

## Open

1. **Lead — contract.** `emergency_tt_min` is required, but the twin has no
   traffic on most of any route to Queen Mary Hospital. Keep it as a
   placeholder, or allow it to be absent?
2. **Data — closure evidence.** Simulation asks for the AID01104 lane
   readings 09:00–09:36, AID01103's congestion onset and AID01106's flow to
   10:35 before another P0. A changed closure is a new scenario file.
3. **Data — diversions.** E refuses P1 and P2 until rerouting is modelled.
   The context offers one detour, the road under the flyover.
4. **9 Oct checkpoint.** With this baseline there is no comparable P0/P1/P2.
