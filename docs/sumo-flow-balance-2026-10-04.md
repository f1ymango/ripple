# SUMO on flow-balance demand: evidence for the 4 October decision

Prepared by Data on 4 October, for Simulation to review and the Lead to decide.
**No file of Simulation's was changed**: this adds two modules beside theirs, two
network patch files and one Data module, and scores with `src/twin/evaluate.py`
as it stands. Checked against Simulation's packet at `38e2edf`
(`docs/sumo-decision-2026-10-04.md` on `sim/e1-evaluation-correctness`), whose
run was reproduced exactly first (66.94%, 41.42%, 2,390 waiting, 53 teleports).

## The result

15 May 2026, 07:55–08:55, no closure at any time, seed 2026. The scored bins are
the 242 count bins and 299 speed bins of Simulation's
`results/twin/oct04-comparison-window.json`, on the same observation file
(same SHA-256).

| Run | GEH < 5 | Speed error (MAPE) | Waiting to enter | Teleports |
|---|---|---|---|---|
| Simulation's packet (fitted detector-to-detector routes) | 66.9% of 242 | 41.4% of 298 | 2,390 of 17,922 (13.3%) | 53 |
| **Flow-balance demand, ordinary-morning speeds** | **96.7% of 242** | **15.7% of 299** | 238 of 16,601 (1.4%) | 0 |
| Same, speeds refreshed from the morning's own previous quarter-hour | 97.5% of 242 | 13.2% of 299 | 335 of 16,601 (2.0%) | 0 |
| Target | at least 85% | about 15% or less | | |

Five seeds (2026, 1, 2, 3, 4): GEH 95.9–97.1%, speed error 15.6–15.7%;
refreshed 96.7–97.9% and 13.2–13.3%. Results:
[ordinary-morning speeds](../results/twin/oct04-flow-balance.json),
[refreshed](../results/twin/oct04-flow-balance-refreshed.json).

The count target is met. The speed error on ordinary-morning speeds is 15.7%:
at the target's edge, not under it. It is under it only with the refresh, which
is a different claim (below).

## Which detectors set demand, and which assess

| Scored on, ordinary-morning speeds | GEH < 5 | Speed error |
|---|---|---|
| The 4 first detectors (AID01101, AID01214, TDSSPWR10001, TDSAPR20001): **demand-setting** | 97.3% of 37 | 10.4% of 47 |
| The other 21: **assessment only** | 96.6% of 205 | 16.6% of 252 |
| All 25, without the 08:50 bin (it holds the accident's first minute) | 96.8% of 217 | 15.7% of 274 |

Only the four first detectors feed 15 May's own counts into the model. Every
join, exit and speed comes from the four clean Fridays in the six weeks before
(8 May, 24 Apr, 17 Apr, 10 Apr; 1 May and 3 Apr are public holidays). No
detector inside a chain is fitted to 15 May, and no speed from 15 May goes in.

With the refresh, every detector's own speed from the quarter-hour before goes
in, so no detector is held out for speed; the hold-out is in time (15 minutes
ahead). That is what a live twin would do. It is not a calibration from
ordinary mornings and should not be quoted as one.

## What is different from the packet's run

1. **Demand** ([`src/twin/flow_balance_demand.py`](../src/twin/flow_balance_demand.py),
   from [`src/loaders/twin_inputs.py`](../src/loaders/twin_inputs.py)). The rule
   of the backup network: traffic enters upstream of each chain's first detector
   at that detector's 15-minute counts; between neighbouring detectors the
   ordinary mornings' net change joins by the on-ramps the network has in that
   stretch or leaves by its off-ramps, by lane count. This answers note 8 in `notes-from-data.md` and
   the packet's own diagnosis (routes starting on detector edges, 84% of the
   backlog at two of them).
2. **Speeds.** Each chain edge moves at the ordinary mornings' quarter-hour speed
   of the detector it leads to, through a variable speed sign. The speed is the
   vehicle-weighted harmonic mean of the 5-minute speeds (the travel-time mean).
3. **Network**, two patches applied to a copy
   ([connections](../sim/scenarios/aberdeen-flow-balance.con.xml),
   [edge cut](../sim/scenarios/aberdeen-flow-balance.edg.xml)):
   - the tunnel toll plaza towards Wan Chai had three lanes with no onward
     connection, so one approach lane of two reached the tube (the "lane without
     an onward connection" in the packet). All four plaza lanes now lead on;
   - edge `1198101443` holds AID01106 at its start and AID01107 near its end; it
     is cut so each detector's stretch can carry its own speed.
   Nothing else differs: one edge cut in two, four connections added, one moved, no signal changed.
4. **Driver settings**: `speedFactor 1`, `speedDev 0.05`, `sigma 0`. The speeds
   given already hold the drivers' spread; SUMO's default adds its own on top.

Not changed: the loops, the observations, the evaluator, the step length, the seed.

## Other days: the same pipeline, nothing retuned

Each day is built from its own clean days of the same weekday in the six weeks
before (no public holiday, no corridor message in Special Traffic News in the
window). "Existing pipeline" is `fit_demand` + `diagnose_preincident` at
`38e2edf`, refitted to each day's own counts.

| Day and hour scored | Days built from | Existing pipeline: GEH / speed / teleports | Flow balance: GEH < 5 | Speed error | Refreshed | Waiting to enter | Teleports |
|---|---|---|---|---|---|---|---|
| Mon 23 Mar, 07:10–08:10 (before IN-26-02105) | 4 | 69.1% / 31.3% / 68 | 97.4% of 269 | 10.2% | 10.1% | 689 of 16,435 (4.2%) | 0 |
| Fri 17 Apr, 07:55–08:55 | 4 | 65.5% / 37.4% / 110 | 93.0% of 200 | 14.9% | 14.3% | 226 of 17,016 (1.3%) | 0 |
| Fri 24 Apr, 07:55–08:55 | 5 | 74.0% / 66.7% / 70 | 93.7% of 223 | 54.5% | 23.1% | 252 of 16,207 (1.6%) | 0 |
| Sat 2 May, 10:55–11:55 (before IN-26-03030) | 3 | 66.8% / 31.7% / 60 | 93.0% of 229 | 10.3% | 11.3% | 593 of 15,275 (3.9%) | 0 |
| Fri 8 May, 07:55–08:55 | 4 | 57.7% / 41.3% / 97 | 97.3% of 111 | 19.5% | 17.3% | 354 of 16,356 (2.2%) | 0 |
| Fri 22 May, 07:55–08:55 | 4 | 62.2% / 32.1% / 81 | 97.3% of 259 | 13.9% | 10.9% | 182 of 16,735 (1.1%) | 0 |
| Fri 29 May, 07:55–08:55 | 4 | 68.2% / 42.2% / 50 | 92.5% of 173 | 23.4% | 21.8% | 82 of 17,018 (0.5%) | 0 |
| Fri 29 May, 11:35–12:35 (before IN-26-03744) | 4 | 77.0% / 43.4% / 38 | 93.0% of 230 | 22.7% | 20.9% | 420 of 15,925 (2.6%) | 0 |
| Fri 5 Jun, 07:55–08:55 | 4 | 66.1% / 44.2% / 126 | 95.4% of 174 | 19.7% | 21.7% | 93 of 17,048 (0.5%) | 0 |
| Tue 18 Aug, 01:30–02:30 (before IN-26-05951) | 4 | 99.4% / 24.3% / 7 | 99.4% of 176 | 15.9% | 18.8% | 0 of 2,776 | 0 |
| Tue 1 Sep, 11:10–12:10 (before IN-26-06391) | 4 | 85.2% / 37.3% / 51 | 97.4% of 196 | 27.5% | 17.4% | 901 of 14,549 (6.2%) | 0 |
| Wed 16 Sep, 07:55–08:55 | 3 | 68.2% / 38.1% / 116 | 97.7% of 214 | 16.6% | 17.8% | 266 of 17,539 (1.5%) | 0 |
| Sun 20 Sep, 15:00–16:00 | 4 | 81.2% / 31.0% / 53 | 96.9% of 224 | 11.1% | 11.2% | 952 of 15,597 (6.1%) | 0 |
| Mon 21 Sep, 07:55–08:55 | 4 | 67.4% / 44.2% / 75 | 97.9% of 236 | 20.7% | 18.8% | 65 of 17,641 (0.4%) | 0 |
| Mon 21 Sep, 17:30–18:30 | 4 | 86.0% / 61.9% / 27 | 98.6% of 143 | 21.4% | 18.4% | 176 of 16,985 (1.0%) | 0 |

Over these 15: GEH < 5 is 92.5–99.4% (median 97.3%) and passes 85% on all 15,
against 3 of 15 for the existing pipeline (median 68.2%). No run teleports a
vehicle. **Speed error is 10.2–54.5% (median 19.5%) and is at or under 15% on
5 of the 15**, against 24.3–66.7% (median 38.1%) before. The refresh lowers it
on 10 of the 15 and raises it on 5. Per-case reports:
[results/twin/flow-balance-cases/](../results/twin/flow-balance-cases/).

So the count result holds across weekdays and times of day. The speed result
does not reach the target in general, and the reason is the next section's
first point.

## What the headline scores hide

- **The speed error is the day-to-day difference, not SUMO.** On 15 May the
  input speeds alone, with no simulation, score 15.2% against the detectors;
  SUMO scores 15.7%. Predicting each of 11 clean Fridays from the others gives
  10–18% (one at 52%), and two halves of the same 5-minute bin differ by about
  7% on their own. On 15 May a third of the error is AID01106 (72%: a queue
  before the tunnel from 08:00 to 08:40 that most Fridays do not have) and
  AID01216 (48%: a queue that cleared at 08:10). A model built from other days
  cannot know either. Tuning SUMO further will not move this figure.
- **The speeds are put in, not produced.** A slow stretch is slow because its
  speed sign says so, not because SUMO formed the queue. The speed score shows
  the inputs are right for the day. It does not show that SUMO reproduces queue
  formation, spillback or recovery. None of this validates the incident replay
  or any diversion.
- **One on-ramp still holds vehicles outside**: the signal-controlled merge on
  the Wong Nai Chung Gap flyover (ramp edge `46766432`, the join between
  AID01108 and AID01109). 238 vehicles on 15 May, up to 952 (6.1%) on other
  days, which is over Data's proposed gate of 1% waiting on 12 of the 16 runs.
  The network gives the ramp's signal and the flyover lane's signal the same
  program, green together, with the ramp giving way. The real timings are in no
  source we hold. Alternating the two half and half cleared 15 May's backlog
  but not other days' (555 still waiting on 20 Sep), so it is not adopted. Counts at
  AID01109 run 14% low on 15 May, partly for this reason and partly because
  more traffic joined there that morning than on the ordinary ones.
- **AID01106 carries 23% more than observed** on 15 May (1,230 against 998):
  the model lets through what that morning's queue held back.
- **Assumptions the detectors cannot settle**, each listed by the builder:
  the entry road with only an exit ahead of it (Canal Road flyover, 244383597)
  carries exactly the traffic that leaves there, which matches the slow lane's
  29–34% share at AID01214 but is not measured; +201 veh/h between
  TDSSPWR10003 and TDSAPR10001 is put on the main line because the network has
  no on-ramp there; two changes under 5% with no ramp are left out; where the
  flyover splits and rejoins, traffic is shared by lane count.
- **Few days.** Each day is built from 3–5 others, and which ones matters: on
  the backup network two Fridays gave 16.6% and four gave 18.8% (below). Quote
  a result with the days it was built from.

## The backup network, clean run

The same morning with no closure, for comparison (code on `data/week2-checks`
plus the patch delivered with this note; `results/fallback/`):

| Backup network, 15 May, no closure | GEH < 5 | Speed error | Inside the chains only |
|---|---|---|---|
| As built: 2 ordinary Fridays, one speed per link | 96.7% of 242 | 16.6% | 96.6% / 17.8% |
| 4 ordinary Fridays, one speed per link | 97.5% of 242 | 18.8% | 97.6% / 20.0% |
| 4 ordinary Fridays, quarter-hour speeds | 97.5% of 242 | 16.6% | 97.6% / 16.9% |

The 16.6% reported on 30 Sep depended on which two Fridays were used: with four
it is 18.8%. With quarter-hour speeds the backup network queues back from the
slow AID01216 link to AID01214 and AID01215 (26% and 32% there), because it puts
exits halfway along a link; SUMO, with exits where the map has them, does not.

## Reproduce

Needs SUMO 1.27.1 and Simulation's input archive
(`results/twin/oct04-provisional-replay-inputs.zip` on their branch) extracted
at the repository root, and the detector cache for the five mornings.

```powershell
python -m src.loaders.fetch twin-inputs --day 2026-05-15 --ordinary-day 2026-05-08 2026-04-24 2026-04-17 2026-04-10
netconvert -s sim/work/aberdeen.net.xml -x sim/scenarios/aberdeen-flow-balance.con.xml -e sim/scenarios/aberdeen-flow-balance.edg.xml -o sim/work/aberdeen.flow-balance.net.xml --lefthand true --output.street-names true
python -m src.twin.flow_balance_demand --inputs sim/scenarios/twin-inputs_20260515.json --network sim/work/aberdeen.flow-balance.net.xml --out sim/work/flow-balance
python -m src.twin.run_flow_balance --inputs-dir sim/work/flow-balance --network sim/work/aberdeen.flow-balance.net.xml --loops sim/work/may-diagnostic/detectors.add.xml --observations sim/scenarios/detectors.json --out results/twin/oct04-flow-balance.json
```

Add `--refresh` to the first command for the refreshed inputs
(`twin-inputs_20260515_refreshed.json`). Another day or hour: give
`twin-inputs` its `--start`, `--end`, `--scored-from`, `--scored-to`,
`--own-until` and `--refresh-until`, export that hour with `twin-detectors`,
and pass `--begin` and `--end` to `flow_balance_demand`.

Run in Linux with Python 3.13; a Windows run has not been made. Tests:
`tests/test_twin_inputs.py`, `tests/test_twin_flow_balance.py`.

## For the decision

- SUMO on these inputs passes the count target on every day tried and reaches
  the speed figure the inputs allow. It is no longer behind the backup network
  on the no-closure hour; the two are driven by the same Data products.
- Neither model is validated for the incident. The next check is the same for
  both: queue reaching each upstream detector, flow while closed, recovery.
- For Simulation to review before any of this is relied on: the two network
  patches, the entry-road rule, the main-line join, the driver settings, and
  the merge signals.
