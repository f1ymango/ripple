# Simulation handoff and calibration review — 4 October 2026

Checked remote main at `4875a85`. The Lead has moved the model decision to
**Monday 5 October evening HKT**. The results freeze remains 14 October.
This note supplies Simulation's status for Visuals; it does not promise other
owners' delivery dates or approve a model on their behalf.

## What Visuals can use now

| Deliverable | Confirmed status and location |
|---|---|
| Reproducible original no-closure SUMO diagnostic | Branch `sim/e1-evaluation-correctness`: `results/twin/oct04-provisional-replay-inputs.zip`, manifest beside it, and `docs/sumo-decision-2026-10-04.md`. Provisional network; not incident validation. |
| New Data no-closure evidence | Main, merged PR #43: `docs/sumo-flow-balance-2026-10-04.md`, `results/twin/oct04-flow-balance.json`, and `results/twin/oct04-flow-balance-refreshed.json`. Data reports 96.7% GEH / 15.7% speed MAPE for ordinary-morning inputs. These are attributed saved results, not independently reproduced by Simulation in this update. |
| New Simulation boundary experiment | Simulation branch: `results/twin/oct03-boundaries.json`, `oct03-boundaries-comparison.json`, `oct03-boundaries-delivery.json`, and `oct04-boundary-experiment-inputs.zip`. Run on 3 October; reviewed here on 4 October. See [diagnosis](calibration-boundaries-2026-10-04.md). |
| Validated full incident P0 | **Not ready.** No accepted queue formation, closure-flow and recovery validation. |
| Feasible diversion and working rerouting/compliance | **Not validated.** Connected detector-chain paths are not reviewed diversion OD routes or evidence of compliance behaviour. No comparable intervention run was produced here. |
| Real matching P0/P1/P2 with original provenance sidecars | None in the checked main tree under `results/runs/`; main still has no `src/evaluator/` implementation. Data/E must confirm any newer off-main artifacts. Main's tracker still identifies fallback PR #35 as unaccepted. |
| Reviewed context, plans and bilingual briefing | D/F code and model-free checks are on main. `docs/lead-pipeline-handoff.md` lists the required C/E route/context and provenance inputs. No real generated set appeared under `data/generated-plans/` or `results/briefing/` in the checked tree. The mock fixtures are not demo results. Lead must confirm a reviewed real set. |
| Console | Main includes PR #41 and `src/console/OPERATOR_WORKFLOW.md`. Observed playback is usable; trajectory replay needs trajectories bound to the evaluated runs. |

## Simulation review of Data's new result

This is a substantial new count result, not a continuation of the 66.94%
packet with one variable changed. Code/report review identifies demand
allocation, imposed speed profiles, driver parameters, network connections
and warm-up changes. The default new replay begins 07:25 (30-minute warm-up,
5,400 simulation seconds); our controlled experiment retains 07:40 and 4,500
seconds. The scored observation hour is still 07:55–08:55.

The following must remain visible before acceptance:

1. The connection patch adds/moves tunnel lane connections without an external
   lane-movement source in the patch. It connects lane 0 of `1198101424`, where
   our cached OSM audit records `motor_vehicle:lanes=no|yes|yes|yes`. Review the
   physical lane/access interpretation before calling this a source-confirmed
   network repair. A lane drop is not automatically a missing connection bug.
2. The builder injects a join on the main line where no mapped ramp exists,
   and allocates other approaches/exits by lane count. These are disclosed
   model assumptions, not measured turning flows. They do not meet this task's
   restriction against adopting unsupported access/OD assumptions merely to
   raise GEH.
3. Variable speed signs impose detector-derived ordinary-day speeds. The lower
   MAPE does not demonstrate endogenous queue formation or incident recovery.
   `sigma=0`, `speedFactor=1` and `speedDev=0.05` also need justification; mean
   input speeds alone do not measure a driver distribution.
4. Data reports 238 vehicles waiting (1.4%) and zero teleports for its primary
   run. Ramp queues remain, and ordinary-day speed MAPE is 15.7%, above the
   nominal 15% gate. The refreshed 13.2% run uses each detector's preceding
   quarter-hour speed and supports a different, time-forward prediction claim.
5. The new report's statement that further SUMO tuning cannot change speed
   error is too strong. Its input-speed comparison describes this prescribed-
   speed implementation; it is not a lower bound on a queue-producing model.

These observations do not invalidate every use of Data's prototype. They
limit its current claim to a promising, explicitly conditioned no-closure
replay pending review. The high count score cannot approve incident benefits.

## Remaining handoff and dates

- **Available now:** source-hashed Simulation experiment and this review packet
  on the simulation branch; Data's saved evidence and console workflow on main.
- **By the scheduled 5 October review:** Lead/Data/Simulation should resolve
  the network/entry assumptions, compare matching windows and coverage, and
  select the model and allowed claims. This is the recorded decision date,
  not a promise that full incident validation will be finished that evening.
- **Before E/Visuals receive accepted simulation results:** agree the initial
  lane and full closure timing; run P0 against closure and recovery readings;
  verify upstream queue/spillback and conservation; review diversion routes,
  controls and compliance; generate matched P0/P1/P2 with original sidecars and
  FCD provenance. C cannot manufacture those E/D/F deliverables.
- **Full incident/plan-results handoff date:** not responsibly estimable until
  the above model and source issues are resolved. Record an owner-agreed date
  at the 5 October review; escalate scope reduction if it threatens 14 October.

Recommendation: do not consume Week 3 indefinitely chasing the original SUMO
fit. Review Data's improved pipeline and fallback with their assumptions
explicit. If incident behaviour cannot be established, narrow the video to
observed playback and clearly labelled illustrative simulation; do not show
unvalidated plan rankings or delay/emissions savings as measured benefits.

This note is published in the repository. No team-channel message was sent.
