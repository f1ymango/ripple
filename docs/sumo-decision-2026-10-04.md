# SUMO evidence for the 4 October decision

Prepared by Simulation on 3 October. Checked team main at `962a5b3`, including
Data's flow-balance, free-flow-speed and entry-route notes. Lead owns the final
integration decision. Recommendation: **SUMO is currently a no-go for validated
quantitative plan comparisons.** Evaluate the clean fallback run separately;
do not accept it automatically. If neither meets the agreed criteria, narrow
the demonstration to observed playback and explicitly illustrative scenarios,
without validated delay savings or plan-ranking claims.

## Latest reproducible no-closure calibration

The instrumented replay exactly reproduced the earlier network-speed run's
evaluation, inserted/waiting counts and teleport totals. It completed all
4,500 simulated seconds with seed 2026 and a 180-second wall-time limit.
No closure was applied at any point; the incident in the config is used only
to bound the pre-incident horizon by `diagnose_preincident`.

| Measure | Latest SUMO result | Decision criterion |
|---|---:|---|
| GEH < 5 | 66.94%, 162/242 eligible count bins | At least 85% |
| Speed MAPE | 41.42%, 298 scored bins | Approximately 15% or less |
| Eligible measured-speed bins | 299 | One lacks simulated speed |
| Unmatched eligible count bins | 0 | Explicit coverage |
| Vehicles loaded / inserted | 17,922 / 15,532 | Disclose actual delivery |
| Waiting to enter | 2,390 (13.34% of loaded) | Unresolved entry queues |
| Still running at horizon | 1,547 | Horizon ends before network drains |
| Teleports | 53: 41 jam, 7 yield, 5 wrong-lane | Unresolved physical flow |

The earlier capped-speed reference scored 66.53% GEH and 36.94% speed MAPE,
with 68 teleports. Removing the ungrounded vehicle speed cap did not produce
an acceptable baseline. Adaptive insertion and a source-derived passenger-lane
restriction were tested independently and worsened teleport totals to 71 and
73. Neither is adopted. No passing SUMO result exists among these experiments.

## Comparable windows, filters and fit/assessment roles

- Physical replay: 07:40–08:55 HKT on 15 May 2026. Warm-up: 07:40–07:55
  (simulation seconds 0–900). Score only 07:55–08:55, with five-minute slots
  starting 07:55 through 08:50. The end is exclusive.
- Counts: at least 40% archive coverage and at least 90% valid lane readings;
  null bins are not zero. There are 242 eligible bins across 25 detectors.
- Speeds: use positive measured speeds supplied by the export. The export's
  speed rule differs from the count coverage rule. Zero-vehicle speeds are
  unmeasured and unscored; valid zero counts remain scoreable.
- All 25 count-eligible detectors and the same pre-incident hour were used to
  fit demand and assess counts. **There are no held-out detectors.** Speed
  observations were not fitting targets in the count-only fitter; however,
  model choices have been assessed against these results, so they are not an
  independent held-out validation either.
- [Machine-readable eligibility and detector lists](../results/twin/oct04-comparison-window.json)
  specify the exact eligible detector/timestamp pairs and observation hash.
  Data should report its demand-setting and assessment sets separately and
  score the intersection when producing an apples-to-apples comparison.
  Disclose omitted detectors and speed bins rather than compare percentages
  with different denominators silently.
- Data's proposed additional gate of less than 1% waiting and no wrong-lane
  teleports is not yet an agreed contract. SUMO currently fails both proposed
  conditions anyway. A clean fallback run must apply no closure before or
  within this window; the existing 08:54 closure contaminates its last bin.

## Flow and boundary diagnosis

The new trip trace reconciles exactly to SUMO's 15,532 inserted and 2,390
undeparted vehicles. Of those waiting, 1,421 originate at edge `136461565`
(AID01214, 23.24 m long, detector at 0.55 m); 590 originate at `814979901#0`
(AID01103). Together these account for 84.14% of the insertion backlog.

The AID01214 origin has two incoming roads (`244383597`, `46108739`), but
the generated routes start at the detector edge. This agrees with Data's
diagnosis that detector-to-detector origins do not represent joining side-road
traffic properly. Aggregate detector differences support net joining/exiting
flow; they do not uniquely determine the split between individual entry roads.
Simply increasing fitted demand would risk increasing insertion queues.

Five detector pairs have identical candidate-route crossing signatures,
including AID01106/07 on edge `1198101443`. An edge-membership fit cannot
distinguish their positions or explain different target totals through route
weight changes alone. Junction placement, travel times, missing observations
and actual entry/exit opportunities must be reviewed before interpreting the
difference as a new origin.

The tunnel audit also records inconsistent OSM lane-access counts and a
passenger-allowed lane without an onward connection. A source-based restriction
experiment did not resolve the overall problem. Repeated physical placement
issues, three lane-count conflicts and three absent May-window detector scopes
remain. Teleports can bypass queues and entry backlogs can suppress corridor
flow, undermining delay and diversion comparisons even when some GEH bins pass.

## Feasibility before Week 3

Evidence packaging, source review and focused diagnostics are achievable now.
A defensible entry/exit demand redesign needs mapped connections, justified
flow allocation, refitting and repeated count/speed/queue checks. We cannot
credibly promise that this reaches both thresholds by tomorrow without taking
time from next week's integration. Recommend time-boxing further SUMO work
behind the fallback/demo decision, not treating these remaining tasks as quick
parameter tuning.

## Incident assumptions are a separate review

On the recorded network, edge `44419212` is the flyover towards Aberdeen
Tunnel; Slow Lane maps to index 0, Fast Lane to index 1. Data proposes Slow
Lane first, supported by sparse lane readings, but it remains an assumption
and its default/override/insufficient-evidence policy is not agreed.

Proposed P0 phases: 08:55 initial closure (sim 4500), 09:36 all lanes (6960),
10:02 reopening (8520), run through 10:35 (10500). These await agreement.
TD's first message is 09:01; operator intervention cannot precede available
information. Detector evidence suggests severe blockage before the all-lanes
message; the 09:36 phase should not be presented as measured physical onset.

Still required: lane/timing sensitivity, queue formation and spillback against
upstream detectors, zero-count closure bins, clearance and recovery lag, and
flow conservation during closures. Diversion paths, capacity, compliance and
counterfactual plan benefits have not been validated. Passing no-closure
calibration alone would not settle any of these questions.

## Reproduction inputs and commands

The [provisional input archive](../results/twin/oct04-provisional-replay-inputs.zip)
includes the exact scenario, SUMO network, original OSM extract, detector export,
loops and CSV mapping, fitted routes, candidate routes and diagnostic report.
Its [manifest](../results/twin/oct04-provisional-replay-inputs.manifest.json)
lists SHA-256 hashes. This shares the diagnostic network for review; it is
**not** the reviewed canonical `sim/aberdeen.net.xml` release. Raw TD snapshots
are not bundled; the frozen observed export is sufficient to repeat scoring.

Use a fresh Windows checkout of the simulation branch containing this packet,
Python 3.14.3 and SUMO 1.27.1. Install the repository requirements, ensure SUMO
is on PATH, then extract at that checkout's root. Do not extract over another
working setup. Run from the root (choose a new work directory on repeat runs):

```powershell
Expand-Archive -LiteralPath results/twin/oct04-provisional-replay-inputs.zip -DestinationPath . -Force
python -m src.twin.diagnose_preincident --config sim/work/oct02-calibration/network-speed.json --observations sim/scenarios/detectors.json --work sim/work/review-oct04 --out results/twin/review-oct04.json --timeout 180 --trace-flow
python -m src.twin.audit_route_delivery --config sim/work/oct02-calibration/network-speed.json --diagnostic results/twin/review-oct04.json --out results/twin/review-oct04-delivery.json
```

Saved evidence: [instrumented run](../results/twin/oct02-flow-trace.json),
[route attribution](../results/twin/oct02-route-delivery.json),
[prior controlled comparisons](calibration-experiments-2026-10-02.md).
The archive passed its integrity check and its primary files were checked
against the recorded run hashes. The traced run reproduced reference results
exactly; a fresh-checkout replay has not been run. No test suite was rerun for
this decision packet.
