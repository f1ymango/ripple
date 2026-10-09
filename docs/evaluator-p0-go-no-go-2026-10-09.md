# IN-26-03365 P0: go/no-go for comparing plans (9 October)

Asked for by the Lead on 9 October, after
[#54](https://github.com/f1ymango/ripple/pull/54) kept public claims to the
observed playback. The question: can E's replay P0 be the baseline that
Lead-generated plans are compared against, and briefed from, before the
14 October results freeze?

**Data's position: NO-GO for comparing or ranking plans by 14 October.** The
P0 stays an internal diagnostic. Visuals and Impact should keep the
observed-only scope. Simulation's review is in section 4; this is not a joint
decision until it is filled in.

The evidence is the replay P0, seed 2026, clearance 66, compliance 50%
([result](../results/evaluator-rehearsal/runs/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.json),
[run report](../results/evaluator-rehearsal/evaluator/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.report.json)),
and [the replay note](evaluator-replay-2026-10-08.md). The bin tables below
come from that run's `evaluation.json`, which `src/twin/evaluate.py` wrote.

## 1. Summary

| Check | Finding | Holds up plan comparison? |
|---|---|---|
| Validation targets | Whole run 89.29% GEH < 5, 14.54% speed error: both met. Before the closure 96.77% / 13.99%. **During the closure 82.02% GEH**, under 85% | Partly: the closure, where plans act, is the phase that misses |
| Speed refresh | 20 detectors' signs, on 97 edges, show the speed the road had on 15 May a quarter-hour earlier. With ordinary-morning signs the speed error is 16.75% (missed). Where the model makes the speed itself, 31.24% | **No.** P1 and P2 inherit the do-nothing morning's speeds on those 97 edges, so a plan cannot change speed there. The detour and the queue stretch carry no refreshed sign |
| Scene assumptions | 4.7 km/h past the scene, 7 km/h crawl, 20 minutes at one lane after 10:00, 6.5 m vehicles. The speed pass depends on three of them (crawl 10 km/h: 16.61%; one-stage reopening: 16.06%; 5 m vehicles: 16.06%). AID01104's raw readings show both flyover lanes in use from 10:04, against the 20-minute narrowing | Only after Simulation's review. None has a source beyond the detectors it was set from |
| Tunnel-side flow and mapping | During the closure the model sends 8 to 47 vehicles a bin past AID01106 against 65 to 122 observed. 36 of the 65 failing count bins are AID01106 to AID01109. AID01106's placement on edge `1198101443` is already questioned in Simulation's map review | **No.** Where diverted traffic rejoins is exactly where the model is most wrong |
| Queue timing | The queue reaches AID01103 about 5 minutes early (09:00 bin: model 12 km/h, observed 51; 09:05: 5 and 14; both about 6 from 09:10) and AID01102 10 to 15 minutes early (09:05: model 8, observed 64; observed only falls to 20 at 09:15) | Mostly. Early by one or two bins |
| Queue recovery | AID01103 is back above 55 km/h at 10:20 in both. But the model releases two surges, at 10:00 (AID01103: 181 vehicles against 75) and at 10:20 when E's second lane reopens (AID01103: 216 against 122; AID01104: 160 against 77) | **No** for the 10:20 surge: it comes from the 20-minute assumption the raw readings contradict |
| Ramp backlog | 448.7 of P0's 1,702.1 vehicle-hours (26%) are vehicles waiting to enter at the tunnel on-ramp `46766432`, which queues with no closure too. In P1 at 70% it cancels the plan's whole gain; at 100% compliance P1 comes out 8.3% worse than P0 because of it | **No.** It moves the plan ranking |
| Wrong-lane teleport | 1: vehicle `f145.50` at 08:59:04 on `1198059119_1`, the fast lane approaching the fork, while the slow lane was closed. Plus 2 jam teleports (09:27:40 and 09:27:59) | Fails Data's proposed rule of no wrong-lane teleports. Small in itself |
| Seed noise | P0 alone moves 3.1% (one standard deviation) between seeds. The rehearsal plans differ from P0 by 1 to 5% | **No** single-seed ranking; several seeds per plan at least |

## 2. Why no-go and not "go with caveats"

Three of the findings would change which plan comes out best, not just by how
much: the ramp backlog, the tunnel side, and the refreshed speeds that P1 and
P2 cannot move. Each is a model or input question that Simulation owns. Fixing
any of them means new inputs, a new P0, a new review, the Lead's plans, and
their runs, all before 14 October. That leaves no time for the review to mean
anything.

What still holds and can be said internally: the replay reproduces the
morning's counts and speeds before the closure, and the queue's arrival and
recovery at AID01103 to within one or two five-minute bins.

## 3. What would turn it into a go (after the freeze, or if Simulation is faster)

1. **Tunnel side:** Simulation confirms where AID01106 stands and which
   traffic joins after the flyover. Re-run P0; the closure-phase GEH should
   reach 85%.
2. **On-ramp `46766432`:** no backlog in the no-closure run, or its waiting
   reported apart from the incident's delay.
3. **Speeds for plan runs:** P1 and P2 run with ordinary-morning signs, or with
   signs only where no plan can change the speed, and P0 is scored the same
   way. If that misses 15%, say so (03-architecture.md §4).
4. **Reopening:** replace the 20-minute narrowing with what AID01104 shows
   (both lanes from 10:04), and see whether the 10:20 surge goes.
5. **Teleports:** no wrong-lane teleport.
6. **Seeds:** each plan on at least five seeds, ranked only if the gap
   exceeds the spread.

When P0 passes these, the hand-off to the Lead is ready to run (section 5).

## 4. Simulation's review

To be filled in by Simulation: agree or disagree with each row of section 1,
and the go/no-go.

| Check | Simulation's view |
|---|---|
| Scene assumptions | |
| Speed refresh | |
| Tunnel-side flow and AID01106 mapping | |
| Queue timing and recovery | |
| Ramp backlog `46766432` | |
| Wrong-lane teleport | |
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
