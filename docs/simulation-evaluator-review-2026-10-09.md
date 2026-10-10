# Simulation technical review of Data's 8 October P0

Reviewed on 9 October HKT from Data revision `3b67a1b`. Simulation's decision
is recorded in [section 4 of the shared review](evaluator-p0-go-no-go-2026-10-09.md#4-simulations-review):
**no-go for public plan comparison by 14 October**. This note supplies the
physical/code checks and one untested candidate for Data's bounded rerun.

## Input identity and what has actually been checked

The P0 packet network hashes to
`eb006b4ea09f01246ea53f163d68854e47b1be0410943f587d846388ef053e9d`.
The rebuilt demand hashes to
`5cbf6f6c93807fd413b9148dce75c769d747a8234ef3ff0bd04c6fe4643b955e`,
and refreshed signs to
`a8734743f90363ef9a7eedbb0f99e3ed2f9cac0c0411d15818f9087f1c9b8792`.
Windows initially wrote CRLF; normalising those two generated XML files to LF
reproduced Data's byte identities. `verify_result` accepted the committed P0,
plan and generation inputs, and `capture_inputs` matched **every** simulation
input in its original sidecar, including E's code. No result was rewritten.
The existing evaluator tests passed: **81 passed**. These are software checks,
not physical validation.

The [generated approach audit](../results/twin/oct09-evaluator-approach-audit.json)
records exact connections, source OSM tags, the ramp signal, lengths and file
hashes. Reproduce after extracting the existing P0 packet:

```powershell
python -m src.twin.audit_evaluator_approach `
  --network sim/work/p0-replay/network.net.xml `
  --osm <the cached aberdeen_bbox.osm.xml with the audit's SHA-256> `
  --out results/twin/oct09-evaluator-approach-audit.json
```

## AID01106 and traffic after the flyover

The registry describes Wong Chuk Hang Road near Hong Kong Academy of Medicine,
eastbound, at 22.25044211 N, 114.1718782 E. Our existing placement is **0.10 m
on `1198101443`**, the two-lane tunnel entrance. The source audit's lane-0
offset is **20.73 m** and the projection is at an endpoint. The preceding
`1198101497` is four lanes in both OSM and SUMO while the feed reports two;
that is a reason for reviewing a two-lane cross-section, not proof that the
selected endpoint is correct. AID01107 is farther along the tunnel on the
split piece `1198101443.40`. Its flow deficit as well as AID01106's means
moving one detector cannot by itself establish a complete fix.

After flyover edge `44419216`, surface edge `1198059128` joins at
`714996652`; Ocean Park Road `26560290#0` joins at `86289334`, before the
tunnel. The surface route also receives connections from Nam Long Shan Road
and Tong Bin Lane. There is no independent incident-window volume for those
entries in the reviewed inputs. The **new E replay already reroutes** at
full closure, unlike the older Simulation diagnostic. Its remaining shortage
must be reviewed as missing local demand, constrained surface discharge,
placement or a combination; it is not solved merely by enabling rerouting.
Do not infer a new flow from AID01106 and then score it as held-out evidence.

## Ramp mechanism and ranking risk

`46766432` (178.47 m) leads to `46766434#1` (20.03 m), then the very short
`485146396` (0.20 m), then `1194711693`. Both ramp lanes enter with minor
priority `m`; the mainline from `462275986#1` has priority. Signal
`11030048926` upstream is compiled as 80 s green, 5 s yellow, 5 s red.
More mainline traffic can therefore reduce ramp gaps even with a long green.
This is a plausible explanation for rising entry delay when P1 sends more
vehicles towards the tunnel. It is not proof that real priority or capacity
is wrong. The short edge is a junction representation, not proof of a
physical 20 cm ramp or permission to add connections.

The 448.7 veh-h entry delay and the plan-ranking reversal are material.
Keep that delay visible. A separate incident-free counterfactual and an
entry-by-entry breakdown can diagnose it, but deleting all ramp delay from
the objective would also delete a possible real consequence of diversion.
No priority/signal correction is source-supported for Monday.

## Scene, recovery and speed interpretation

The 4.7 km/h passage speed is fitted to detector throughput; 7 km/h on the
approach uses AID01103's same-incident speeds. They can describe a calibrated
replay but cannot independently validate capacity or predicted queues there.
The 20-minute one-lane stage is not supported as a physical closure across
the whole flyover edge: the raw feed has both lanes carrying traffic at
AID01104 from 10:04. A restriction before that detector remains possible,
but its location and duration are not measured. Do not transform that
possibility into a 10:20 reopening fact. Data's existing one-stage sensitivity
is already evidence that removing the stage changes fit; a labelled all-open
by 10:04 sensitivity is feasible if another recovery diagnostic is needed.
Use 6.5 m only as an unverified fleet assumption and show the existing 5 m
sensitivity. Neither value is justified by selecting the better score.

The open-road 66 km/h also comes from detector speeds; the OSM tags say
50 km/h. It is a calibration choice pending a speed-limit/source check.
For counterfactual P0/P1/P2, use common ordinary-day signs or justify each
unaffected refreshed edge. A SUMO variable speed sign changes the lane speed
limit, so congestion can still make traffic slower; it does not prescribe
every realised speed. However, incident-day limits can constrain the speed
improvements a plan is meant to predict. The 16.75% ordinary-sign result is
the relevant reported miss, not a reason to borrow the 14.54% replay pass.
[SUMO speed-sign documentation](https://sumo.dlr.de/docs/Simulation/Variable_Speed_Signs.html).

## Wrong-lane teleport: concrete candidate, no claimed fix

`f145`'s generated route crosses the flyover. The audit shows three lanes on
`1198059119`, so `_1` is the **middle lane**. Its only forward connection is
to `1198059120_1`, whose only forward connection is `44419212_0` (closed slow
lane). Approach `_2` connects to the open `44419212_1` fast lane. The 77.11 m
move-over warning starts on `1198059119`, leaving one late lane change amid
the queue. The network has an open-lane path; the evidence suggests late
lane-change feasibility rather than demonstrating a missing physical link.
The vehicle's full trajectory/lane-change state is still needed to prove the
individual cause. [SUMO's wrong-lane definition](https://sumo.dlr.de/docs/Simulation/Why_Vehicles_are_teleporting.html).

Prepared [earlier-move-over.json](../sim/scenarios/evaluator-diagnostics/earlier-move-over.json)
extends awareness to existing edge `814979901#0`: 330.96 m of approach edges.
It changes no road connection, input demand, closure phase or speed. It is
an awareness-distance sensitivity, not an observed warning sign or accepted
scene parameter. The scenario passed E's schema check. To run only this P0:

```bash
python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal --plan P0 --scenario sim/scenarios/evaluator-diagnostics/earlier-move-over.json --compliance 0.5 --clearance 66 --results-dir results/simulation-review-oct09-move-over
```

Apply an external 240-second wall guard including startup (for example GNU
`timeout 240s`); keep the standard 11,400-second horizon and report failure if
the wall guard expires. E's internal timer starts after TraCI connects and
does not bound startup retries. Compare against the existing replay, including
all teleports, flow, recovery and waiting; removing one teleport cannot accept
P0 or resolve tunnel/ramp bias.

## Failed local launches and Monday handoff

Two control-launch attempts failed before a TraCI connection and were stopped
when SUMO repeatedly exited. The shorter-worktree retry had an outer
240-second timeout. A direct zero-horizon launch exited with code
`0xC0E90002` and no output; even `sumo --version` failed, including outside
the restricted shell. Thus this is a local executable/startup blocker, not
evidence against the scenario. No simulation second or new validation score
is claimed, and the candidate was not run. The earlier path-length suspicion
was not established. Data can use the prepared scenario on its working SUMO
installation by Monday 12 October and review it Tuesday 13 October.

Reopening and warning-distance checks are feasible; a measured surface input,
physically confirmed detector cross-section and ramp-priority correction
cannot be promised from current evidence. Retain the agreed no-go for public
plan comparison and the observed-only scope while those questions remain.

## 10 October independent bounded replay

SUMO 1.27.1 subsequently started normally. Simulation reconstructed the
committed P0 inputs from Data's packet and checked the network, demand and
speed-sign hashes against the original provenance sidecar before running.
Both runs used seed 2026, compliance 0.5, clearance 66, the same 11,400-second
horizon and an external 240-second wall guard. The control command was:

```powershell
python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal --plan P0 --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --compliance 0.5 --clearance 66 --results-dir results/simulation-review-oct10-control
```

The sensitivity used the command above with `--scenario
sim/scenarios/evaluator-diagnostics/earlier-move-over.json --results-dir
results/simulation-review-oct10-move-over`. The external wall guard covered
the entire subprocess, including TraCI startup. Both completed to 11,400 s
within the guard (187.8 s control, 135.7 s sensitivity). Their generated
[control result](../results/simulation-review-oct10-control/runs/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.json),
[control report](../results/simulation-review-oct10-control/evaluator/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.report.json),
[sensitivity result](../results/simulation-review-oct10-move-over/runs/2026-05-15_ABD_P0_c50_t66_earlier-move-over_rehearsal.json)
and [sensitivity report](../results/simulation-review-oct10-move-over/evaluator/2026-05-15_ABD_P0_c50_t66_earlier-move-over_rehearsal.report.json)
are accompanied by their original generated provenance sidecars in the same
`runs/` directories. These are internal diagnostics, not accepted results.

| Measure | Control | Earlier awareness |
|---|---:|---:|
| Whole-run GEH < 5 / count bins | 89.29% / 607 | 88.79% / 607 |
| Closure-phase GEH < 5 / count bins | 82.02% / 267 | 82.02% / 267 |
| Whole-run speed MAPE / speed bins | 14.54% / 787 | 13.94% / 787 |
| Speed MAPE where model makes speed | 31.24% / 115 | 27.39% / 115 |
| Total delay | 1,702.1 veh-h | 1,713.1 veh-h |
| Waiting to enter at ramp `46766432` | 448.7 veh-h | 452.5 veh-h |
| Vehicles waiting to enter at end | 96 | 129 |
| Teleports: wrong lane / jam | 1 / 2 | 1 / 0 |
| Maximum queue, AID01103 path | 1,095 m | 1,094 m |

The control independently reproduces Data's scores and wrong-lane event.
The longer warning removes two jam teleports, but `f145.50` still teleports
from `1198059119_1` at 08:59:04. This rejects earlier warning **alone** as a
fix. The unchanged 82.02% closure score, persistent tunnel-side discrepancy,
and slightly higher ramp waiting leave P0 **NO-GO** for plan ranking. The
original 9 October failed-launch account above remains an accurate dated log.
The vehicle's lane trajectory and an independently observed local entry flow
would be needed before changing connections or adding demand. A reopening
sensitivity may examine the 10:20 surge, but its score alone cannot settle
the detector cross-section, ramp control or counterfactual speed signs.
