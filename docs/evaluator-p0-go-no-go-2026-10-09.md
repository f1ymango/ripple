# IN-26-03365 P0: go/no-go for comparing plans (9 October, updated 10 October)

Asked for by the Lead on 9 October, after
[#54](https://github.com/f1ymango/ripple/pull/54) kept public claims to the
observed playback. The question: can E's replay P0 be the baseline that
Lead-generated plans are compared against, and briefed from, before the
14 October results freeze?

**Joint position: NO-GO for comparing or ranking plans by 14 October.**
Data (9 and 10 October) and Simulation (section 4, 9 and 10 October) agree.
Visuals and Impact should keep the observed-only scope; the Lead retains the
scope and integration decision.

What changed on 10 October, after Simulation's review of `3b67a1b`: Data
found and corrected two simulator artefacts
([the 10 October note](evaluator-replay-fixes-2026-10-10.md)). P0 is now
better: it meets both targets in all six seeds, and its pre-crash ramp
backlog is gone. But the corrections also showed that the 8 October plan
gains came from those artefacts. Corrected, both rehearsal plans add delay,
and **whether P2 adds or saves delay depends on how the north on-ramp is
modelled**, which is one of Simulation's blockers. The answer stays no-go.
Simulation's view of the two corrections is asked for at the end of section 4.

The evidence is the corrected replay P0, seed 2026, clearance 66, compliance
50% ([result](../results/evaluator-rehearsal/runs/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.json),
[run report](../results/evaluator-rehearsal/evaluator/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.report.json)),
five more seeds and the one-change runs in `results/evaluator-diagnostics/`.
Bin figures come from the run's `evaluation.json`, written by
`src/twin/evaluate.py`.

## 1. Summary

| Check | Finding, 10 October (9 October in brackets) | Holds up plan comparison? |
|---|---|---|
| Validation targets | Whole run **89.45% GEH, 14.44% speed error: both met** (89.29%, 14.54%). Five more seeds: 89.45–90.44% and 13.64–14.42%, all met. Before the closure 96.77% / 13.90%. **During the closure 83.15% GEH** (82.02%), still under 85%. As Simulation notes, detectors used to set scene speeds score a calibration fit, not independent validation | Partly: the closure, where plans act, is still the phase that misses |
| Speed refresh | 20 detectors' signs, on 97 edges, still cap speed at 15 May's speed of a quarter-hour earlier (a sign sets a limit; traffic can still go slower). Common ordinary-morning signs, Simulation's preference: **16.94%**. Refreshed only where no plan's traffic goes: 16.29%. Held at the crash: 17.82%. All miss | **No.** The caps can stop a plan improving on the do-nothing speed. Without them the target is missed |
| Scene assumptions | 4.7 km/h past the scene, 7 km/h crawl, 20 minutes at one lane after 10:00, 6.5 m vehicles, 40% of drivers leave. The pass depends on three of them: 5 m vehicles give 15.60%, a one-stage reopening 15.78%, 50% leaving 15.29%. It no longer depends on the crawl (10 km/h: 91.43%, 14.94%). Simulation rejects the 20-minute stage and wants 5 m and 6.5 m both shown: on its preferred one-stage reopening, P0 misses the speed target | **No**, on Simulation's review |
| **Correction 1, 10 Oct: the detour** | SUMO had sent 96 Canal Road-bound drivers into Happy Valley streets, which jammed until the end of the run and blocked the tunnel exit. Drivers now go round by Wong Chuk Hang Road and keep their route | Yes. **Fixed**; needs Simulation's review as an assumption |
| **Correction 2, 10 Oct: the north on-ramp** | The ramp's merge held vehicles up to 27 minutes from 07:45, before the crash (448.7 veh-h, 26% of P0's delay), while AID01109 counted 19% under the detector. The join now enters on the main line. But with the merge kept and only correction 1, the backlog grows to 762.5 veh-h and the plans change sign: P1 +1.4%, P2 **−2.7%**. Simulation warns ramp delay may also be a real effect of diversion | **No:** P0's backlog is gone, but the plan ranking depends on how the ramp is modelled |
| Tunnel-side flow and mapping | During the closure the model sends 47 vehicles a bin past AID01106 (33) against 90 counted, and 46 past AID01108 (11) against 96. 32 of the 64 failing count bins are AID01106 to AID01109 | **No.** Plans divert traffic to exactly where the model is most wrong |
| Queue timing | Unchanged: the queue reaches AID01103 about 5 minutes early and AID01102 10 to 15 minutes early (09:05: 6 km/h in the model, 64 measured). This is the largest part of the fair-sign speed error | Mostly. Early by one to three bins |
| Queue recovery | AID01103 back above 55 km/h at 10:20 in both. Two surges remain: at 10:00 (AID01103: 185 against 75) and at 10:20, when E's second lane reopens (AID01103: 206 against 122; AID01104: 162 against 77) | **No** for the 10:20 surge: it comes from the 20-minute assumption the raw readings contradict |
| Wrong-lane teleports | **3** (1): `f145.50` 08:59:04 on `1198059119_1`; `f145.80` 09:05:34 and `f146.78` 09:10:40 on `1198059120_2`, all on the last edges before the fork, where drivers must reach the detour's lane | Fails Data's proposed rule of none. Small in itself |
| Seed noise | Paired by seed, six seeds at 50%: P1 − P0 **+8.5%** (95% interval +7.0 to +10.1), P2 − P0 **+4.2%** (+3.2 to +5.2), P1 − P2 +4.3% (+3.1 to +5.5); same sign in all six. P0 alone moves 1.4% (3.1%) | **Yes**, for seed noise. Model bias remains, as Simulation notes |
| What the plans do | Advised drivers stop taking the Aberdeen exits and queue for the one detour, which is full; the queue reaches the network entry and more drivers are kept out (P1 at 50%: 616 against 356). Delay in the network rises with both plans, with or without correction 2. The ranking holds whatever a leaver is charged (0 to 90 minutes) | **No:** the effect runs through the drivers-leave rule (40% share and the entry rule, calibrated, not sourced), lands on the tunnel side, and P2's sign turns on the ramp |

## 2. Why still no-go

The ranking is stable across seeds, but what decides it is not yet
trustworthy:

- **The ramp decides P2's sign.** With correction 2, P2 adds 5.2%; with the
  ramp's merge kept, it saves 2.7%. Neither ramp representation is
  source-supported for plan runs (Simulation, section 4).
- **The plans act through the drivers-leave rule.** How many drivers turn
  away at the Aberdeen exits, and when drivers give up at the network entry,
  were calibrated to two detectors, not observed. That rule decides whether
  advice helps or hurts.
- **Their traffic lands on the tunnel side**, where the model sends about
  half the vehicles counted and the closure phase misses 85%.
- **With speeds that plans cannot inherit, the speed target is missed**
  (16.94% with common ordinary signs), and so it is on Simulation's preferred
  one-stage reopening (15.78%).

Each of these needs Simulation's review, a re-run, and then the Lead's plans
and their runs, all before 14 October.

What can be said internally now: the corrected replay reproduces the morning
before the crash (96.8% / 13.9%) and meets both targets over the whole run in
all six seeds. In this model the only detour is already full during the
closure, so advice that just points drivers at it adds delay inside the
network; whether it adds delay overall depends on the ramp. That is a finding
about the model, not yet about the road.

## 3. What would turn it into a go

1. **Tunnel side:** Simulation finds where the extra traffic past AID01106
   came from. The candidates are in section 3 of the
   [10 October note](evaluator-replay-fixes-2026-10-10.md). The closure-phase
   GEH should reach 85%. *Open.*
2. **On-ramp `46766432`:** *P0's pre-crash backlog removed by correction 2,
   but the plan ranking still depends on the ramp. Open: evidence on the
   real merge priority and capacity, and paired no-closure/P0 runs as
   Simulation asks.*
3. **Speeds for plan runs:** P0, P1 and P2 on common ordinary-morning signs,
   or refreshed signs justified edge by edge, at or under 15%. *Open: 16.94%
   ordinary, 16.29% refreshed only off the plans' roads. Most of the gap is the
   back of the queue (item 4 and Queue timing).*
4. **Reopening:** replace the 20-minute narrowing with what AID01104 shows
   (both lanes from 10:04). *Open: done alone it misses the speed target
   (15.78%), so it goes with item 3.*
5. **Teleports:** no wrong-lane teleport. *Open: 3.*
6. ~~**Seeds.**~~ *Done for seed noise: six paired seeds, intervals above.
   Model bias is not touched by more seeds.*
7. **New, the drivers-leave rule:** Simulation agrees the 40% share and the
   entry rule, or a source replaces them.

## 4. Simulation's review

Reviewed by Simulation on 9 October against Data branch commit `3b67a1b`.
The recorded P0 result, plan and generation-input provenance verified; every
simulation input hash matches the locally reconstructed files and E code.
This verifies input identity, not an independent successful rerun. The local
SUMO executable failed before startup, including on `sumo --version`; the
launch attempts produced no scored run. Details and the bounded candidate
command are in [Simulation's technical review](simulation-evaluator-review-2026-10-09.md).

**10 October update:** SUMO 1.27.1 became available and Simulation completed
independent, bounded control and earlier move-over runs using the verified
inputs. The control reproduces Data's headline scores and the same wrong-lane
teleport. Moving awareness from 77.11 m to 330.96 m still teleports `f145.50`
at 08:59:04 on `1198059119_1`. Closure count GEH remains 82.02%; ramp-entry
waiting rises from 448.7 to 452.5 vehicle-hours. The comparison and generated
run artifacts are in [the technical review](simulation-evaluator-review-2026-10-09.md).
The failed 9 October launch statement above is retained as dated history.

| Check | Simulation's view |
|---|---|
| Validation targets | **Agree on the reported scores; disagree that the whole-run pass accepts P0.** Closure GEH is 82.02%, and the scores on detectors used to set scene speeds are calibration fit rather than independent validation. |
| Scene assumptions | **Change before any acceptance.** Keep 4.7 and 7 km/h only as explicitly fitted replay parameters, not measured capacities or independent queue predictions. Reject a physical one-lane closure through 10:20: both lanes carry traffic at AID01104 from 10:04. That does not rule out a restriction elsewhere, but no source locates one. Use the existing one-stage diagnostic and, if needed, a labelled 10:04 all-open sensitivity. Neither 6.5 m nor the 5 m default is a measured fleet mix; retain both as sensitivity cases, not a selected value because it passes MAPE. |
| Speed refresh | **Agree with the no-go for counterfactual plans using incident-day speed caps on affected roads.** Technical correction: a variable speed sign sets a limit; traffic may go slower, so it does not fix every realised speed. It can nevertheless cap a plan's improvement at the do-nothing speed. Use the same ordinary-morning inputs for P0/P1/P2, or justify that refreshed edges cannot be affected by any plan. Report the 16.75% ordinary-sign error as a miss; do not inherit the 14.54% replay claim. |
| Tunnel-side flow and AID01106 mapping | **Agree; physical placement is not confirmed.** The model places both loops at 0.10 m on `1198101443`, at the tunnel entrance, 20.73 m from the registry point. The nearby upstream road has four model lanes; the feed has two. This supports a candidate tunnel cross-section but cannot certify it. Surface Wong Chuk Hang Road and Ocean Park Road connect after the flyover, with additional surface entries; their incident volumes are unknown. E now reroutes during full closure, so Simulation's older finding of no through-surface routes does not fully explain this newer run. No invented join or relocation is approved. |
| Queue timing and recovery | **Agree on the discrepancies, but reject “mostly” as acceptance.** One or two bins matter to intervention timing; the 7 km/h approach is prescribed from the same observations. The 10:20 surge is tied to an unsupported second opening. Remove that stage for a diagnostic and compare lane readings, both upstream detectors, flow and recovery through 10:35; a smooth curve alone is insufficient. |
| Ramp backlog `46766432` | **Agree it blocks ranking.** The compiled two-lane ramp feeds minor-priority connections into `1194711693`; mainline connections have priority. That can starve the ramp as diverted traffic rises. The 80/5/5 signal upstream does not remove the downstream merge conflict. Actual priority, control and demand still need evidence. Qualify section 3: zero no-closure backlog is not required if real queues exist, and merely subtracting ramp waiting cannot validate the whole-corridor ranking. Report it separately and compare paired no-closure/P0 cases without hiding plan-induced spillback. |
| Wrong-lane teleport | **Agree it remains a failed diagnostic check.** Correct section 1's lane label: `1198059119_1` is the **middle** of three approach lanes. It connects via `1198059120_1` to the closed flyover slow lane `_0`; approach `_2` leads to the open fast lane `_1`. The 330.96 m warning sensitivity completed on 10 October with no connection edit; the same vehicle teleports on the same lane at the same second. Earlier warning alone is therefore insufficient, and the individual lane-change cause remains unresolved. |
| Seed noise | **Agree that one seed cannot support ranking.** Use paired P0/P1/P2 seeds and uncertainty on each plan-minus-P0 difference. The six paired signs are useful diagnostic evidence; comparing a benefit only with P0's standalone standard deviation is not a formal acceptance test. Model bias remains even with more seeds. |
| **Go / no-go** | **NO-GO for comparing or recommending plans by the 14 October freeze.** Agree with Data and retain observed-only public scope (#54). The awareness-distance diagnostic has now run and failed to clear the wrong-lane check or closure flow gap. A reopening sensitivity is still possible by Monday 12 October, but no evidence currently supports promising a physically reviewed tunnel mapping, new local flow or ramp-priority correction by then. A Tuesday 13 October review can examine any new evidence; no headline score improvement alone reverses this decision. |

Simulation agrees to **one provisional surface detour in this model**:
Wong Chuk Hang Road under the flyover, using the exact `replace`/`with` edge
lists in `evaluator_IN-26-03365_replay.json`. This is graph feasibility, not a
public recommended route or proof that it is the only real-world alternative.
The Tong Bin Lane **+20 s green remains an assumed network control**; no
real signal timing or operator authority has been established. Retain that
label in context, plans, results and any illustration. No route or incident
assumption here authorises public benefit claims.

### Data's 10 October follow-up

Simulation's rows above review `3b67a1b`, before the two corrections. Since
then the replay has changed in ways that touch three rows, and Data asks for
Simulation's view on them:

| 10 October change | Data's evidence | Simulation's view |
|---|---|---|
| Correction 1: drivers turned away go round by Wong Chuk Hang Road and keep their route (`closure.detour`, the exact `replace`/`with` edges Simulation agreed above) | SUMO's own rerouting sent 96 of 111 vehicles on the Wong Nai Chung Road exit, all Canal Road-bound, into Happy Valley streets that jammed until the end of the run; AID01108 counted 11 a bin in the model, 96 real | |
| Correction 2: the AID01108→AID01109 join enters on the main line, not by ramp `46766432` | Pre-crash backlog from 07:45 (448.7 veh-h) while AID01109 counted 19% under the detector. Without it, P0's ramp waiting grows to 762.5 veh-h and P2's sign flips | |
| The drivers-leave rule (40% at the exits, the entry rule), through which both plans now act | Calibrated to AID01101 and AID01102; no source | |
| Wrong-lane teleports, now 3 (`f145.50`, `f145.80`, `f146.78`) | All on `1198059119`/`1198059120` before the fork | |

## 5. Hand-off to the Lead, when P0 is accepted

Already in place on this branch, so nothing waits on Data:

- **Context:** [IN-26-03365_first-report-v2.json](../data/plan-context/IN-26-03365_first-report-v2.json),
  reviewed. On 9 October its `sources` lost a file that was never committed
  (`sim/scenarios/evaluator_IN-26-03365_signals.add.xml`). The +20 s at Tong
  Bin Lane is marked an assumed network control there and in the scenario.
  One route only, "Wong Chuk Hang Road", the only detour the network has.
- **A distinct result namespace:** `--plan-set` puts the plans folder's name
  in every `run_id`, for example `..._P1_c50_t66_replay_lead-v1`. The
  rehearsal results are in `results/evaluator-rehearsal/` and stay there;
  `results/runs/` is empty and reserved for the Lead's set. Before keeping an
  existing result, `batch` checks it binds the same plans, generation inputs
  and simulation inputs, and stops if not. So rehearsal results cannot be
  reused under the Lead's plans.
- **The command**, once the Lead's plans are saved and pass
  `src.plans.run --check-only`:

  ```bash
  python -m src.evaluator.batch --plans <the Lead's plans folder> --plan-set lead-v1 \
      --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --clearance 66
  ```

  It writes P0, P1 and P2 at 30%, 50% and 70% into `results/runs/`, each with
  its sidecar. F's `--check-only` then takes the three files of one compliance
  level.
- **For the plans themselves:** with one detour that is already full, a plan
  that only points drivers at it adds delay inside the network in this model.
