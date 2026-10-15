# Tuen Mun bet: evidence update for the 16 Oct go/no-go (Data, 15 Oct 2026, 11:40 HKT; share tests added 15:10)

This updates `docs/tuen-mun-go-no-go-evidence-2026-10-14.md`. Every number below is in:
- `results/tuen-mun-lead-grid-oct15-p0x-merge-at-site/` (`comparison_p0x-merge-at-site.json`, from `scripts/tuen_mun/report.py`);
- `results/tuen-mun-p0-variants-oct15/`.

The run plan, frozen before any run, is `docs/tuen-mun-p0-variants-and-lead-grid-2026-10-15.md`, parts C and D.

## Which P0
**`p0x-merge-at-site`:** replay-v2, except that drivers move over on the 250 m approach.

**Why this one:**
- Of every P0 tried (Simulation's five variants, replay-v2 and Data's candidates), it is the only one that meets validation v2 on every seed.
- Calibration seeds 2026–2028 all pass.
- So do all 18 fresh-grid P0s: GEH 86.3–88.7%, free-flow speed error 13.8–14.0%, congestion state 91.5–92.1%, no stray wrong-lane teleport, nobody left waiting to enter.
- It removes replay-v2's collapse into one lane and the Sham Tseng gridlock at 18:00–18:15.

**What it still gets wrong:**
- **The queue.** Between Sham Tseng and the crash site it reads 41–43 km/h, against TD's 20.6. The open lane stands still while the lanes shut ahead keep moving: lane-speed spread 36–37 km/h, against TD's 6.0.
- **Clearing.** The queue clears early.
- **Discharge.** After the reopening the model discharges 6,100–6,200 veh/h, against TD's 4,560–4,896.

Merging in turn fixes the lane balance in the model, but it cuts throughput past the site below TD's, so no version met v2. Simulation's review criteria are therefore **still not met**, and a P2 result here is a candidate, not a measured saving.

## The Lead's plan set on fresh seeds
- **Plan set:** `IN-26-02615-lead-capacity-oct15`, unchanged.
- **Grid:** seeds 2029–2031, compliance 0.3/0.5/0.7, vehicle-actuated and fixed-time Sham Tseng signals.
- **Delay measure:** E's delay with Castle Peak Road's longer drive charged, at 0, 4 and 10 min per driver who left at Ting Kau.

| Signals | Seed | Compliance | P2 vs P0 (0 / 4 / 10 min outside) | P2 cars on Castle Peak Rd | P1 vs P0 (4 min) |
|---|---|---|---|---|---|
| actuated | 2029 | 0.3 | -4.6% / -4.6% / -4.5% | 61 | -19.4% |
| actuated | 2029 | 0.5 | -4.3% / -4.4% / -4.6% | 102 | +21.9% |
| actuated | 2029 | 0.7 | -9.8% / -9.7% / -9.6% | 140 | +64.6% |
| actuated | 2030 | 0.3 | +1.9% / +1.4% / +0.7% | 59 | -5.4% |
| actuated | 2030 | 0.5 | -3.3% / -3.5% / -3.9% | 102 | +34.0% |
| actuated | 2030 | 0.7 | -2.8% / -3.4% / -4.3% | 149 | +65.8% |
| actuated | 2031 | 0.3 | -2.9% / -3.1% / -3.4% | 66 | -2.4% |
| actuated | 2031 | 0.5 | -2.6% / -3.1% / -3.8% | 110 | +23.3% |
| actuated | 2031 | 0.7 | -5.3% / -5.7% / -6.3% | 147 | +67.0% |
| fixed-time | 2029 | 0.3 | -3.7% / -3.7% / -3.7% | 63 | +21.2% |
| fixed-time | 2029 | 0.5 | -5.2% / -5.3% / -5.4% | 106 | +62.3% |
| fixed-time | 2029 | 0.7 | -2.5% / -2.9% / -3.5% | 137 | +82.8% |
| fixed-time | 2030 | 0.3 | -8.4% / -8.0% / -7.5% | 63 | +10.0% |
| fixed-time | 2030 | 0.5 | -3.3% / -3.6% / -4.0% | 100 | +49.2% |
| fixed-time | 2030 | 0.7 | -2.0% / -2.5% / -3.3% | 146 | +73.7% |
| fixed-time | 2031 | 0.3 | -2.6% / -2.7% / -2.8% | 65 | +5.9% |
| fixed-time | 2031 | 0.5 | -0.3% / -0.9% / -1.8% | 112 | +61.5% |
| fixed-time | 2031 | 0.7 | -0.0% / -0.8% / -2.0% | 149 | +100.1% |

**P2 (11% of the Tsuen Wan & Ting Kau → Tuen Mun group via Castle Peak Road):** lower than P0 in **51 of 54** cell × outside-minute cases. Range −9.8% to +1.9%, median −3.5%.
- **Fixed-time signals:** 27 of 27 lower (−8.4% to −0.0%). Note that seed 2031 at 0.7 is −0.0% with no minutes charged outside.
- **The losing cell:** actuated seed 2030 at compliance 0.3, +1.9% / +1.4% / +0.7%, with 59 cars diverted.
- **Under the team's rule** (lower in every cell and every outside value), **P2 does not win.**

**P1 (everyone advised round):** lower than P0 in 9 of 54 cases, all at compliance 0.3 with actuated signals; median +48.2%, up to +101.1%.
- In those cases 30% of the group diverts. At seed 2029 that is −19.4%; at seeds 2030 and 2031 it is −2.4% to −5.4%.
- At compliance 0.5 and 0.7, Castle Peak Road and the Sham Tseng exit overload. The queue backs up to where traffic enters the network: 300–714 vehicle-hours of waiting to enter, against 5–11 in P0.

**Cars diverted, exit queues, teleports:**
- **Cars on Castle Peak Road under P2:** 59–66 at compliance 0.3, 100–112 at 0.5, 137–149 at 0.7.
- **Sham Tseng exit slip, worst 5 minutes of waiting:**
  - actuated: P2 0.1–0.4 veh-h, P0 0.1;
  - fixed-time: P2 0.8–1.3 veh-h, P0 0.4–0.8.
- **Teleports:** 1–16 per run. P2 runs have up to 3 wrong-lane teleports.
- **Waiting to enter:** no P0 or P2 run has anyone still waiting to enter at the end.

## Data's reading
- **A real but small saving that noise can swallow.** The capacity-bounded P2 gives a consistent saving of about 3–5% on this P0. It is never worse with fixed-time signals, unlike the stand-in P2 on replay-v2.
- **Why the rule fails.** At compliance 0.3 only about 60 cars divert. The effect is then small enough that seed noise can flip a cell, which is what happens at seed 2030.
- **What is robust:** "do not send everyone round". P1 is worse than P0 in 45 of 54 cases. Targeted P2 beats P1 in 48 of 54; the exceptions are actuated seeds 2029 and 2030 at compliance 0.3, where 30% of the group actually diverting does better.
- **The share is the lever.** On the first seed, 30% actually diverting gave −19%; 50% gave +22%. The Lead's share (3–8% actually diverting) sits far below that. A calibration-seed sweep of the share is running (part E, share 0.2, seeds 2026–2028) to inform the next plan generation. It is not a candidate.
- **Aberdeen** stays the submission fallback, untouched.

## Added 15:10: a larger share
- **Calibration seeds 2026–2028** (\`results/tuen-mun-share-sweep-oct15/\`): share 0.2 is better than P0 in 18 of 18 cases with actuated signals (median −7.6%) and 15 of 18 with fixed-time signals (median −5.0%).
- **Fresh seeds 2032–2034** (\`results/tuen-mun-share-020-fresh-oct15/\`): 49 of 54 (median −6.7% actuated, −4.2% fixed-time). It fails two cells: actuated seed 2032 at 0.3 (+1.1%) and fixed-time seed 2032 at 0.5 (+4.8%).
- **Averaged over three seeds,** every signal × compliance group is lower than P0 for both shares: 0.11 by −2.1% to −6.3%, 0.2 by −1.3% to −9.3%.
- **Seed noise is the problem.** P0 alone moves by about ±4% from seed to seed: 1,216–1,308 veh-h over seeds 2026–2028. With one run per cell, any plan whose saving is about 5% will lose a cell somewhere.
- **The replay-v2 grid** stopped after two cells. P2 is already worse in one of them, so it cannot change this.

## Data's verdict for 16 Oct
- **No Ripple plan passes the team's every-cell rule on Tuen Mun.** That holds for the Lead's P2 (0.11), Data's share 0.2, and P1.
- **What the evidence supports:**
  - Targeted Castle Peak Road advice lowers delay on average by about 4–5% on the only P0 that meets version 2 on every seed.
  - Advising everyone is worse in 45 of 54 cases.
- **Both of those rest on a P0 whose queue speed Simulation has not accepted.**
- **Our recommendation:**
  - Keep Aberdeen as the submission.
  - Tuen Mun can appear only as supporting evidence for "target, don't broadcast", labelled as a candidate, with no saving claimed.
