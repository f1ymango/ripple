# IN-26-03365: what P0 is, what it must pass, and the evidence verdict (13–14 October)

Prepared by Data in answer to the Lead's request of 13 October evening, for
Simulation's review. It builds on Simulation's root-cause note
(`sim/lead-plans-diagnostic-oct13` at `a48b8c9`), which analysed the 10 October
replay, and checks each point on replay 3.1 with E 3.2 (33 baselines in
`results/evaluator-lead-draft-20261013-b/`). The numbers come from
`p0-checks.json` and `closure-counts.json` there.

## Verdict

| Question | Answer |
|---|---|
| Evaluator workflow (plans → twin → validation → rank or refuse) | **GO.** Unchanged since `docs/evaluator-lead-plans-2026-10-13.md`. |
| Incident P0 as a basis for a measured plan benefit | **NO-GO.** It fails two of the six checks in section 4 in nearly every baseline: traffic reaching the tunnel during the closure, and queue recovery. |
| A second diversion besides Wong Chuk Hang Road | **None usable.** In the network every route that avoids the flyover uses Wong Chuk Hang Road under it. Outside it, the only alternative is the hospital corridor (Pok Fu Lam Road), which P0 keeps clear and for which there is no evidence. |
| The Tong Bin Lane +20 s signal | **Remove.** Its programme is netconvert's guess (24 s green in 90 s); no source gives the real timing or says TD can extend it. |
| Can a source-supported P2 beat both P0 and P1? (PR #67, section 5) | **No.** Without the unverified signal, P2 at the saved shares loses to doing nothing, and at half shares it beats P1 but ties P0 only through the assumed outside delay. Neither earned the reserved confirmation. |
| Plan runs on this replay | **Diagnostic only.** No route recommendation or saving should be stated in the submission from them. |

What would change the verdict is new evidence, not new settings (section 6).

## 1. What P0 is

P0 is **15 May as it happened, with no plan action**:

- **The closure, as the detectors show it.** One lane shut from 08:54. Both lanes shut from 09:00:30, when AID01104 on the flyover goes empty. The road reopens at 10:00 (the one-stage reopening), with 10:04 and a four-minute clearing stage as the other cells of the grid.
- **What drivers had to do.** A driver reaching the fork with both lanes shut takes Wong Chuk Hang Road under the flyover, then their own route. This is forced, not advised: it is the only open road. The detectors show it, since AID01103 before the fork kept passing traffic while the flyover was empty, and the tunnel kept counting. **TD's 09:36 message named the same road:** "Motorists are advised to use alternative routes such as Wong Chuk Hang Road". So P0 is neither "no advice" nor a model of TD's broadcast. Drivers did what the closure forced 36 minutes before TD said it, and nobody in P0 changes route because of the message.
- **Drivers already committed** to the last 18 m before the flyover when both lanes shut go on over it.
- **Some drivers leave the corridor at the queue.** The share is 20%, fitted to when the queue reached AID01101, not sourced. Each leaver is charged an assumed 20 minutes outside the network.

P1 and P2 add advice on top of this from 09:01 to 10:00. The advice points to the same road, and it reaches drivers earlier and further upstream, including after the flyover reopens. In the main cell, 461 (P1) and 374 (P2) drivers took the advised route, and 192 and 142 of them were still on it after the reopening.

### Which assumptions have independent support

| Assumption | Support | Status |
|---|---|---|
| Closure timing | AID01104 lane by lane | **Supported** |
| Reopening | AID01104 shows both lanes carrying traffic from 10:04 | **Bounded**: 10:00, 10:04 and a clearing stage are all in the grid |
| Forced detour via Wong Chuk Hang Road | the detectors, and TD's 09:36 message | **Supported**, as the only open road |
| North ramp (flow f22) | merge trade-off measured on other mornings | **Bounded**: both versions are in the grid; not established |
| 20% leave the corridor | fitted to the queue's arrival at AID01101 | **Not independent** |
| 20 minutes outside the network | assumed | **Does not decide anything**: 0 to 40 minutes leaves all three verdicts unchanged |
| 6.5 m mean vehicle length | model choice | **Sensitive**: with 5 m, P2's effect moves from −3% to −18% |
| Demand (Simulation's packet) | flow balance on 15 May | **Wrong where it matters** (section 2) |

## 2. Independent checks

**After-flyover detector placement: correct.** Five of six loops lie 4 to 9 m from TD's published coordinates. AID01106 lies 21 m away, on the tunnel side of the last split. On ordinary days it counts the same stream as AID01107 inside the tunnel, 96 to 102% at 30 km/h or more (`results/data/count-bias_AID01106_AID01107.md`). So the deficit is not a placement error, and AID01107 shows it too.

**Traffic reaching the tunnel: the model is short.** Mean per five minutes in the main P0:

| | 08:00–08:50 measured | 08:00–08:50 model | 09:05–09:55 measured | 09:05–09:55 model |
|---|---|---|---|---|
| AID01103, before the fork | 153 | 174 | 43 at 6–14 km/h (undercount; about 59–79 real) | 75 |
| AID01104, the flyover | 100 | 113 | 0 | 0 |
| AID01107, in the tunnel | 129 | 126 | 82 at about 60 km/h (reliable) | 63 |

Over the full closure, all 33 baselines send 63 to 79% of the counted traffic at AID01106 to AID01108. Hourly-equivalent GEH is 6.9 to 13.8, against a target of 5. Five-minute GEH passes 8 or more of the 10 bins.

**Where the missing traffic enters: not identifiable from detector totals.** Two roads join between the flyover and the tunnel: the surface road coming back (edge 1198059128, which the detour uses) and an Ocean Park Road slip (26560290#0). Before the closure, the measured gain from flyover to tunnel is 29 per five minutes; the model's is 13, made up by extra flyover traffic. On 37 ordinary weekday mornings the tunnel carries 14 to 21% more than the flyover, and the model is near the low end of that. During the closure, more traffic reached the tunnel than the queue through AID01103 can explain, even allowing for its undercount. It may have come via Ocean Park Road, from Wong Chuk Hang itself, or from drivers who left the queue and came back. Net changes between detectors cannot say which (Simulation's point), and choosing one to fit the score would not validate the road.

**Queues: onset right, recovery too early.** Queue onset is within 10 minutes of measured at all three queue detectors in 18 of 33 baselines, and at AID01103 in 29. Recovery is the problem. The measured queue at AID01102 and AID01103 lasted until 10:15; the model clears it 15 minutes earlier at AID01103 in 32 of 33 baselines (10 minutes in the other), including those reopening at 10:04, and 10 to 15 minutes earlier at AID01102 in 32. That matters, because the plans' cost after the reopening is exactly what the cells disagree on.

**Waiting to enter.** 0.1 to 1.5% of in-scope vehicles are still waiting to enter at the end of the run (6 baselines exceed 1%, the ramp-as-built cells). Entry wait is 21 to 58% of P0's delay, mostly at the one-lane Ap Lei Chau Bridge slip. It is real queueing, but it happens outside the modelled roads, so it is shown on its own in every run report.

**Teleports.** No P0 has a wrong-lane teleport outside a lane shutting or a jam. Jam teleports run from 0 to 14 per P0 and are reported.

## 3. North ramp

Both representations are run as bounds in every grid (Simulation found the plan's sign depends on them in the 10 October replay). With E 3.2 the verdicts hold under both bounds. Which one is right still needs a reviewed source for how the north join operates.

## 4. Checks a revised P0 must pass

`python -m src.evaluator.p0_checks --grid <grid>`. Proposed by Data. Reported, not enforced by F or the console; making them targets is Simulation's and the Lead's call.

| # | Check | Threshold | Passes now |
|---|---|---|---|
| 1 | Validation version 2 | as in `src/validation_targets.py` | 33 of 33 |
| 2 | Traffic after the flyover during the full closure | hourly-equivalent GEH < 5 at AID01106, 07, 08 | **0 of 33** |
| 3 | Queue onset | within 10 min of measured at AID01101, 02, 03 | 18 of 33 |
| 4 | Queue recovery | within 10 min of measured at AID01101, 02, 03 | **1 of 33** |
| 5 | Still waiting to enter at the end | ≤ 1% of in-scope vehicles | 27 of 33 |
| 6 | Wrong-lane teleports | none outside a lane shutting or a jam | 33 of 33 |

Every check must pass in every counting cell before a plan benefit is claimed. Separately, the ranking's verdicts must not change with the outside-delay assumption between 0 and 40 minutes; they do not today.

## 4a. Audit: is a driver selected for advice but not rerouted shielded from leaving?

Yes, slightly. `PlanActions.follows()` counts a driver as following the advice
when their seeded draw selects them, whether or not the reroute was applied, and
`DriversLeave` never lets a following driver leave. An instrumented copy of P1's
main run (debug only, outside `results/`; it reproduced the committed delay,
833.4, exactly) found 339 drivers kept from leaving by the advice. 18 of them
were never rerouted, mostly drivers still waiting to enter. At the 20% leave
share that is about 4 drivers, about 1 vehicle-hour at the assumed 20 minutes,
against P1's 54 vehicle-hours more than P0 in that cell. Not material to any
verdict here. The fix for the next E version is one line: only drivers actually
rerouted (`group_of`) are exempt. It was not changed tonight, because changing
E's code would invalidate the matched runs in progress.

## 5. Matched diagnostic runs of the Lead's P2 diagnostics (PR #67)

Protocol fixed before any run: `docs/lead-p2-diagnostic-protocol-2026-10-13.md`.
The runs used the Lead's own files from PR #67 (hashes checked against its
manifest), 33 screening cells per variant, 198 runs, E 3.2. In both sets P0 and
P1 are identical to `lead-draft-20261013-b` in all 33 cells, so the runs are
deterministic. **Diagnostic: the incident P0 is not accepted.**

Mean per cell over the 33 cells (vehicle-hours; drivers):

| Plan | Took the advised route (still on it after the reopening) | Sent round at the closure | Left the corridor | Delay in network | Waiting to enter | Assumed outside | Total |
|---|---|---|---|---|---|---|---|
| P0 | 0 | 676 | 387 | 497.5 | 312.1 | 130.4 | 940.0 |
| P1, broadcast | 467 (179) | 370 | 374 | 517.7 | 322.4 | 129.7 | 969.8 |
| Saved model P2, 0.8/0.7 + signal | 371 (134) | 435 | 358 | 496.1 | 308.7 | 122.7 | 927.5 |
| `lead-p2-nosignal-oct13`, 0.8/0.7 | 367 (137) | 426 | 374 | 511.4 | 322.8 | 128.8 | 962.9 |
| `lead-p2-half-nosignal-oct13`, 0.4/0.35 | 184 (69) | 547 | 380 | 503.4 | 314.7 | 129.0 | 947.1 |

Verdicts (31 counting cells; seed5 and ramp-seed5 fail on the same P1
wrong-lane teleport in every set), with the outside delay recomputed at 0 to
40 minutes instead of 20:

| Plan set | 0 min | 10 min | 20 min (as run) | 30 min | 40 min |
|---|---|---|---|---|---|
| `lead-p2-nosignal-oct13` | P0 first | P0 first | **P0 first**: P2 +2.8% (95% interval +1.2 to +4.5), P1 +3.5%, P1 and P2 tie | P0 first | P0 first |
| `lead-p2-half-nosignal-oct13` | P0 first | P0 first | P0 and P2 tie: P2 +1.0% (−0.1 to +2.1); P2 before P1 by 2.5%; P0 before P1 | tie | tie |
| Saved model P2 (for comparison) | P0 and P2 tie | tie | tie: P2 −1.4% (−4.1 to +1.2) | tie | tie |

**Answers to the Lead's questions.**
1. *Did the unverified signal drive the result?* **Yes.** With the same shares,
   removing it adds about 35 vehicle-hours per cell (927.5 → 962.9), mostly in
   the network and waiting to enter, and turns a tie with P0 into a clear loss.
2. *Does less early advice help?* It is better than broadcasting (P2 before P1
   at every assumption), but it does not beat doing nothing. Its tie with P0 at
   20 minutes depends on the assumed outside delay: at 0 or 10 minutes, P0 is
   first. By the protocol, that tie is driven by the assumption.
3. *Does any supported P2 beat both P0 and P1?* **No.** Neither variant
   earned the reserved confirmation run, and none was run.

Why, in this replay: advice can only send drivers to the road the closure
already forces them onto, and sooner. Advised drivers join the sole detour
from 09:01, further upstream, and 69 to 179 of them are still on it after the
flyover reopens. That loads the one detour without adding capacity.

For `lead-p2-nosignal-oct13`, the ranking's `first` is P0. F would therefore
draft a "no additional action" briefing if these runs were in `results/runs/`.
They are not: they stay in `results/evaluator-lead-p2-*-oct13/` as diagnostics,
and the submission states no route recommendation or saving.

## 6. What would change the verdict

- **Entry or turning counts** at the Ocean Park Road slip and the surface road's return during 09:00–10:00, or a TD count of tunnel traffic by origin. With those, demand after the flyover can be corrected from a source, then check 2 re-run.
- **The cause of the late recovery**, for example how long recovery vehicles held a lane after 10:00, from TD or the police. With that, the reopening can be modelled from a source, then check 4 re-run.
- **A reviewed source for the north join** (ramp priority, where flow f22 enters).
- **For any signal action**, TD's timing plan and whether it can be changed.

None of these is in any source the team has. Without them, the 15 October pack should use the observed playback and the recorded GenAI workflow, with no route recommendation and no savings figure.

## 7. Comparable runs: recipe and provenance

1. One plans folder per plan set: P0.json, P1.json, P2.json and generation-inputs.json, exactly as the constraint validator returns them. Name it in `--plan-set`; never relabel.
2. One grid file per plan set (`sim/scenarios/rankings/`), listing its cells. The cells must be the same as the set it is compared with.
3. Per cell, run P0 first, then P1 and P2 (`python -m src.evaluator.run ... --results-dir <one folder per plan set>`). E refuses a plan whose P0 was made from other plans, inputs or code.
4. Every result has a provenance sidecar binding the plan, its generation inputs, the scenario, every input file and E's code by SHA-256. Every run report gives health, teleports by kind, drivers sent round and let in, leavers, and the delay in three parts.
5. `python -m src.evaluator.ranking --grid ...` checks every sidecar, refuses mixed code, and writes the ranking once. Then run `p0_checks` and `closure_counts`.
6. The same E commit and the same scenario files for every set compared. Label results diagnostic until P0 passes section 4.
