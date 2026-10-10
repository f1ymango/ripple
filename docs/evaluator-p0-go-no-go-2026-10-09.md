# IN-26-03365 P0: go/no-go for comparing plans (9 October, updated 10 October)

Asked for by the Lead on 9 October, after
[#54](https://github.com/f1ymango/ripple/pull/54) kept public claims to the
observed playback. The question: can E's replay P0 be the baseline that
Lead-generated plans are compared against, and briefed from, before the
14 October results freeze?

**Data's position, 10 October: still NO-GO for comparing or ranking plans by
14 October.** Visuals and Impact should keep the observed-only scope.
Simulation's review is in section 4; this is not a joint decision until it is
filled in.

What changed since 9 October: Data found and corrected two simulator
artefacts ([the 10 October note](evaluator-replay-fixes-2026-10-10.md)). P0 is
now better: it meets both targets in all six seeds, and two of this review's
blockers are gone. But the corrections also showed that the 8 October plan
gains came from those artefacts. Corrected, both rehearsal plans add delay,
and they do it through the two parts of the model that are least sourced.
That is why the answer stays no-go.

The evidence is the corrected replay P0, seed 2026, clearance 66, compliance
50% ([result](../results/evaluator-rehearsal/runs/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.json),
[run report](../results/evaluator-rehearsal/evaluator/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.report.json)),
five more seeds and the one-change runs in `results/evaluator-diagnostics/`.
Bin figures come from the run's `evaluation.json`, written by
`src/twin/evaluate.py`.

## 1. Summary

| Check | Finding, 10 October (9 October in brackets) | Holds up plan comparison? |
|---|---|---|
| Validation targets | Whole run **89.45% GEH, 14.44% speed error: both met** (89.29%, 14.54%). Five more seeds: 89.45–90.44% and 13.64–14.42%, all met. Before the closure 96.77% / 13.90%. **During the closure 83.15% GEH** (82.02%), still under 85% | Partly: the closure, where plans act, is still the phase that misses |
| Speed refresh | 20 detectors' signs, on 97 edges, still show 15 May's speed of a quarter-hour earlier. Fair signs, refreshed only where no plan's traffic goes: **16.29%**, missed by 1.3 points. Ordinary mornings: 16.94%. Held at the crash: 17.82% | **No.** P1 and P2 inherit the do-nothing morning's speeds on those edges. Without them the target is missed |
| Scene assumptions | 4.7 km/h past the scene, 7 km/h crawl, 20 minutes at one lane after 10:00, 6.5 m vehicles, 40% of drivers leave. The pass now depends on three of them: 5 m vehicles give 15.60%, a one-stage reopening 15.78%, 50% leaving 15.29%. It no longer depends on the crawl (10 km/h: 91.43%, 14.94%) | Only after Simulation's review |
| **Correction 1, 10 Oct: the detour** | SUMO had sent 96 Canal Road-bound drivers into Happy Valley streets, which jammed until the end of the run and blocked the tunnel exit. Drivers now go round by Wong Chuk Hang Road and keep their route | Yes. **Fixed**; needs Simulation's review as an assumption |
| **Correction 2, 10 Oct: the north on-ramp** | The ramp's merge held vehicles up to 27 minutes from 07:45, before the crash (448.7 veh-h, 26% of P0's delay). The join now enters on the main line, as AID01109's counts say it did | Yes. **Fixed** (was a blocker) |
| Tunnel-side flow and mapping | During the closure the model sends 47 vehicles a bin past AID01106 (33) against 90 counted, and 46 past AID01108 (11) against 96. 32 of the 64 failing count bins are AID01106 to AID01109 | **No.** Plans divert traffic to exactly where the model is most wrong |
| Queue timing | Unchanged: the queue reaches AID01103 about 5 minutes early and AID01102 10 to 15 minutes early (09:05: 6 km/h in the model, 64 measured). This is the largest part of the fair-sign speed error | Mostly. Early by one to three bins |
| Queue recovery | AID01103 back above 55 km/h at 10:20 in both. Two surges remain: at 10:00 (AID01103: 185 against 75) and at 10:20, when E's second lane reopens (AID01103: 206 against 122; AID01104: 162 against 77) | **No** for the 10:20 surge: it comes from the 20-minute assumption the raw readings contradict |
| Wrong-lane teleports | **3** (1): `f145.50` 08:59:04 on `1198059119_1`; `f145.80` 09:05:34 and `f146.78` 09:10:40 on `1198059120_2`, all on the last edges before the fork, where drivers must reach the detour's lane | Fails Data's proposed rule of none. Small in itself |
| Seed noise | P0 alone moves **1.4%** (3.1%). Both plans add delay in all six seeds: P1 +7.2 to +10.4%, P2 +2.5 to +5.2%; P2 below P1 in all six | **Yes now:** the ranking is not seed noise |
| What the plans do | Advised drivers stop taking the Aberdeen exits and queue for the one detour, which is full; the queue reaches the network entry and more drivers are kept out (P1 at 50%: 616 against 356). The ranking holds whatever a leaver is charged (0 to 90 minutes) | **No:** the effect runs through the drivers-leave rule (40% share and the entry rule, calibrated, not sourced) and lands on the tunnel side |

## 2. Why still no-go

The ranking is now stable, but what decides it is not yet trustworthy:

- **The plans act through the drivers-leave rule.** How many drivers turn
  away at the Aberdeen exits, and when drivers give up at the network entry,
  were calibrated to two detectors, not observed. That rule decides whether
  advice helps or hurts.
- **Their traffic lands on the tunnel side**, where the model sends about
  half the vehicles counted and the closure phase misses 85%.
- **With speeds that plans cannot inherit, the speed target is missed**
  (16.29%).

Each of these needs Simulation's review, a re-run, and then the Lead's plans
and their runs, all before 14 October.

What can be said internally now: the corrected replay reproduces the morning
before the crash (96.8% / 13.9%) and meets both targets over the whole run in
all six seeds. In this model, the only detour is already full during the
closure, so advice that just points drivers at it makes the morning worse.
That is a finding about the model, not yet about the road.

## 3. What would turn it into a go

1. **Tunnel side:** Simulation finds where the extra traffic past AID01106
   came from. The candidates are in section 3 of the
   [10 October note](evaluator-replay-fixes-2026-10-10.md). The closure-phase
   GEH should reach 85%. *Open.*
2. ~~**On-ramp `46766432`.**~~ *Done on 10 October: correction 2.*
3. **Speeds for plan runs:** P1 and P2 run with fair signs, and P0 is scored
   the same way, at or under 15%. *Open: 16.29%. Most of the gap is the back
   of the queue (item 4 and Queue timing).*
4. **Reopening:** replace the 20-minute narrowing with what AID01104 shows
   (both lanes from 10:04). *Open: done alone it misses the speed target
   (15.78%), so it goes with item 3.*
5. **Teleports:** no wrong-lane teleport. *Open: 3.*
6. ~~**Seeds.**~~ *Done: six seeds, the ranking exceeds the spread.*
7. **New, the drivers-leave rule:** Simulation agrees the 40% share and the
   entry rule, or a source replaces them.

## 4. Simulation's review

To be filled in by Simulation: agree or disagree with each row of section 1,
and the go/no-go.

| Check | Simulation's view |
|---|---|
| Scene assumptions | |
| Speed refresh, and fair signs at 16.29% | |
| Correction 1: drivers go round by Wong Chuk Hang Road | |
| Correction 2: the north join on the main line | |
| Tunnel-side flow and AID01106 mapping | |
| Queue timing and recovery | |
| Drivers-leave rule (40%, entry rule) | |
| Wrong-lane teleports | |
| **Go / no-go** | |

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
  that only points drivers at it adds delay in this model.
