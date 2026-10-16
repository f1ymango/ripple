# Tuen Mun: Simulation's P0 variants and the Lead's fresh grid. Run plan, frozen before any run (Data, 15 Oct 2026, 01:30 HKT)

This plan carries out two predeclared requests, without changing either:
- Simulation's predeclared P0 comparison: `docs/tuen-mun-p0-simulation-review-2026-10-14.md`, from `sim/tuen-mun-p0-spike-oct14` at 600c158.
- The Lead's fresh plan grid: `docs/tuen-mun-lead-plans-2026-10-15.md`, at 3db6045.

All inputs below were committed before any of these runs. Nothing changes after outcomes are seen. A change means a new label and a rerun.

## Frozen inputs (sha256, first 12 hex)

| File | sha256 |
|---|---|
| `sim/tuen-mun/network.net.xml` | 97f5a64ba610 |
| `sim/tuen-mun/network-fixed-time.net.xml` | 4bd7241f977b |
| `sim/tuen-mun/network-scene-upstream.net.xml` | 258de014ebe1 |
| `sim/tuen-mun/network-scene-downstream.net.xml` | 9e448d1b5087 |
| `sim/tuen-mun/demand_20260415.rou.xml` | 6bab6f898fab |
| `sim/tuen-mun/demand_20260415-no-residual.rou.xml` | 7716b383403e |
| `sim/tuen-mun/observations_20260415.json` | 415a66fd2daa |
| `sim/tuen-mun/detectors.add.xml` | 1759e7265a5e |
| `sim/tuen-mun/detectors-scene-upstream.add.xml` | 47585c4a1886 |
| `sim/tuen-mun/detectors-scene-downstream.add.xml` | 665b6393e1dd |
| Lead plan set `data/generated-plans/IN-26-02615-lead-capacity-oct15/P0.json` | 832b2646e691 |
| Lead plan set `P1.json` | 51cc3ab9b448 |
| Lead plan set `P2.json` (share 0.11) | 0defc99a1f4a |
| Lead plan set `generation-inputs.json` | a8479854edeb |

The evaluator is E as committed on this branch. Its code is unchanged since 4c5db06.

## Part A: Simulation's P0 variants (diagnostic)
- **Results:** `results/tuen-mun-p0-variants-oct15/`.
- **Plan set:** `IN-26-02615-p0-only`.
- **Every variant:** seeds 2026, 2027 and 2028, clearance 59 min. P0 does not depend on compliance, so each run uses 0.5.

| Simulation # | Label | One change from replay-v2 |
|---|---|---|
| 1 | `p0v-reference` | none (rerun; the 1,141 removed Ting Kau drivers stay, labelled as a fitted residual) |
| 2 | `p0v-scene-up` / `p0v-scene-down` | the same 250 m scene and approach at the upstream end (2,605–2,855 m) or the downstream end (2,845–3,095 m) of the TDS90032–33 span |
| 3 | `p0v-middle-open` | the middle lane, not the slow lane, stays open in the one-lane phases |
| 4 | `p0v-td-text` | one lane from 17:59 until the reopening; no 18:17 or 18:41 change |
| 5 | `p0v-no-residual` | the 1,141 are not removed. Own diversion only through the queue-triggered Route 3 rule, share 0.2 as before. Demand is not rebalanced. |

**Reported per variant and seed** (`scripts/tuen_mun/p0_variants_report.py`):
- 5-minute counts at TDS90024/29/32/33/34, against TD's counts with their coverage and lane validity;
- 5-minute speeds at the queued detectors;
- queue onset, tail extent and clearance at each detector;
- discharge after the reopening at TDS90033;
- the Sham Tseng exit backlog and waiting to enter;
- teleports, with count and location;
- a vehicle ledger: loaded, inserted, arrived, still driving, waiting, left at Ting Kau by exit;
- Route 3 and Castle Peak Rd flows.

**Selection**, as Simulation set it:
- A variant is credible only if it fixes the queue and recovery disagreement without an unexplained flow deficit or teleport.
- No variant is chosen on aggregate GEH alone.
- The residual-removal variant only bounds the sensitivity.

## Part B: the Lead's fresh grid
- **Results:** `results/tuen-mun-lead-grid-oct15/`.
- **Plan set:** `IN-26-02615-lead-capacity-oct15`, which is final and does not change after results.
- **Grid:**
  - seeds 2029, 2030 and 2031, never used before;
  - compliance 0.3, 0.5 and 0.7;
  - Sham Tseng signals vehicle-actuated (`replay-v2-s20xx`) and fixed-time (`replay-v2-fixed-s20xx`);
  - P0, P1 and P2 in every cell: 54 runs.
- **Delay measure:** `scripts/tuen_mun/report.py`, with the longer Castle Peak Rd drive charged and 0, 4 and 10 minutes outside.
- **Also reported:** cars diverted, exit queues, waiting to enter, teleports, and P0's detector and queue checks.
- **Decision rule, unchanged:** P2 is lower than P0 in every cell and under each outside value. P1 is reported the same way.
- **This P0 is replay-v2,** the P0 the Lead's request names. Simulation rates it no-go for a measured ranking (queue too fast, clears about 30 min early). So any P2 result here is a candidate for the 16 Oct review, not a measured saving.
- If a Part A variant turns out credible, the same plan set may be run on it as a further labelled grid. That decision rests on Simulation's criteria, not on plan outcomes.

## Part C: Data's candidates after the variant runs (15 Oct, written before they run)
None of Simulation's five fixes the queue speed, and neither does Data's `p0x-merge-at-site` (drivers learn of the closure on the 250 m approach, not along the 2.45 km edge before it). Lane by lane, every one of those runs shows the same thing at TDS90025–32, 18:00–18:15:
- **Open lane at the scene:** stands still (0–80 veh/h at 1–10 km/h).
- **Lanes shut ahead:** run past it at 45–65 km/h, and their drivers cut in at the end of the approach.
- **Loop speeds:** a loop's speed is the volume-weighted mean over the vehicles that pass, so the moving lanes set it. The standing lane barely registers, which is how the model reads 40–45 km/h.
- **What TD saw:** all three lanes queued at 7–20 km/h, occupancy 60–100% (raw lane readings, `src/loaders/detectors.py`).
- **Knock-on effects:** the standing queue is in the nearside lane, which is also the Sham Tseng exit lane. So the exit's flow fell from about 670 to 36–170 veh/h, and the queue reached the Ting Kau merge in that lane alone.

A network zipper at the scene (diagonal links from each lane into the one beside it) was tried and dropped before any replay. SUMO took the diagonal link even with every lane open, which left the fast lane at the scene empty in ordinary traffic.

| Label | Changes from replay-v2 |
|---|---|
| `p0x-zipper` (+ `-s2027`) | move over on the approach, and E's **first** merging-in-turn rule (commit b597929) |
| `p0x-turn` (+ `-s2027`, `-s2028`) | move over on the approach, and E's **second** merging-in-turn rule (`merge_in_turn`, `src/evaluator/simulate.py` sha256 a870d683b245…, commit ebabb9e) |
| `p0x-turn-sigma05` (+ `-s2027`, `-s2028`) | the same as `p0x-turn`, and drivers' imperfection sigma 0.5 (SUMO's default; the twin had 0), `sim/tuen-mun/demand_20260415-sigma05.rou.xml`. It lowers the flow out of a standing queue. TD measured 4,560–4,896 veh/h at TDS90033 after the reopening; every run so far gave 6,100–6,900. |

**The second merging-in-turn rule:**
- A driver in a lane shut ahead keeps to it along the approach.
- At its end, the driver moves over one lane only when the last driver through that lane's end was one of the lane's own: one each.
- A slow driver fully behind in that lane holds back 2 s, but only if there is room ahead.
- A driver kept 120 s at the end goes at the next room.
- The let-in rule leaves the approach to this rule.

**Why the first rule was replaced:** the two `p0x-zipper` runs fail version 2 (seed 2026: GEH 77.67%, free-flow error 16.33%, 9 wrong-lane teleports, 1 not at a lane shut or a jam). Two faults, both found in a debug replay from 17:59:
- **Lane 2 jumped the queue:** lane 2 drivers moved in ahead of lane 1's own queue.
- **Let-in froze the open lane:** it kept holding drivers beside, not behind, a driver at the lane end, so the open lane stood still and drivers in the shut lanes timed out at the end.

The same replay with the second rule shows all three lanes moving stop-and-go at the approach end and no wrong-lane teleport. The runs with the first rule are kept as they are. The rest of the first rule's set (`p0x-zipper-s2028`, `p0x-zipper-sigma05*`) never ran and is removed.

**sigma 0.5 on ordinary Wednesdays** (`results/tuen-mun-p0-variants-oct15/ordinary-days-driver-imperfection.json`): both days still meet version 2.

| Day | sigma | GEH | Free-flow speed error | Congestion state |
|---|---|---|---|---|
| 22 Apr | 0.5 | 90.38% | 11.38% | 100% |
| 22 Apr | 0 | 97.22% | 10.92% | 100% |
| 6 May | 0.5 | 96.36% | 12.64% | 99.34% |
| 6 May | 0 | 96.67% | 11.53% | 99.34% |

Same criteria as Part A: the queue speed and extent at TDS90024–32, the recovery and the discharge after the reopening, no unexplained flow deficit, no wrong-lane teleport, and the ledger. A candidate is credible only if it meets Simulation's criteria as well as version 2. If one is, the Lead's plan set from Part B runs on it as its own labelled grid (`results/tuen-mun-lead-grid-oct15-<label>/`), with the same seeds, compliances and decision rule.

### Part C outcome (15 Oct, 04:25)
**Result.** Merging in turn spreads the queue across the lanes, but no version keeps the site's throughput, so none meets version 2. Only `p0x-merge-at-site` meets version 2 on all three seeds.

**Runs with results** (`results/tuen-mun-p0-variants-oct15/`):

| Run | Seeds | GEH | Free-flow error | Congestion state | Wrong-lane teleports (other) | Delay, veh-h | Verdict |
|---|---|---|---|---|---|---|---|
| `p0x-merge-at-site` | 2026–2028 | 87.79–89.28% | 13.80–13.95% | 91.69–92.17% | 0 | 1,234–1,306 | meets version 2 |
| `p0x-zipper` (first rule) | 2026, 2027 | 77.67% (2026) | 16.33% | 91.03% | 1 | 2,239 | fails |
| `p0x-turn` (second rule) | 2026–2028 | 82.14–82.73% | 14.17–14.76% | 91.98–92.36% | 0 | 1,587–1,665 | fails on counts |
| `p0x-turn-sigma05` | 2026–2028 | 80.05–81.84% | 18.9–19.7% | | | 3,359–3,665 | rejected |

- **`p0x-turn`, why it fails on counts:** throughput past the site falls to 1,188–1,212 veh/h with one lane open (TD 1,584–1,740) and to about 2,780 with two open (TD 3,024–3,096).
- **`p0x-turn-sigma05`, why rejected:** 140–249 drivers are still waiting to enter at the end of the run.

**Development runs, versions 3–6 of the rule** (seed 2040 only, not results; side branch `data/v3-dev`, commit 9ac15d7):
- Drivers in a lane shut ahead keep to it from the Sham Tseng exit on.
- The lane-speed spread at TDS90025–31 falls from about 38 to 18 km/h; TD reads 6.0.
- Speeds there fall to 12–30 km/h, against TD's 8–20.
- Throughput past the site with one lane open stays at 1,270 veh/h or collapses, and GEH is 70.8–81.3% in every version.
- A 0.5 s start-up delay meets version 2 on both ordinary Wednesdays: 22 Apr GEH 96.71%, 6 May 96.97%. On the incident day, though, it stalls the merge.

**What is left for Simulation (C):** SUMO's lane-change model does not form a three-lane queue behind a lane closure while keeping the site's measured throughput. In every P0 here, the queue's speed at TDS90024–31 is set by the lanes that keep moving. Treat the queue speed and the clearing time as unresolved.

## Part D: the Lead's plan set on `p0x-merge-at-site` (written before it runs)
- **Why this P0:** of every P0 run so far, it is the only one that meets version 2 on all three seeds. It also removes replay-v2's single-lane collapse and the Sham Tseng gridlock.
- **Known faults:** it still has the faults in Part C (queue speed, clearing time, discharge after the reopening). So a P2 result on it is a candidate for the 16 Oct review, not a measured saving.
- **Scenarios:** `p0x-merge-at-site-s2029/2030/2031`, actuated signals, and `p0x-merge-at-site-fixed-s2029/2030/2031`, fixed-time signals. Each is identical to `p0x-merge-at-site` apart from its seed and signal network.
- **Grid:** the same plan set, compliances and decision rule as Part B; 54 runs into `results/tuen-mun-lead-grid-oct15-p0x-merge-at-site/`.
- **Then:** Part B's grid on replay-v2, into `results/tuen-mun-lead-grid-oct15/`.

## Part E: a share sweep on the calibration seeds (15 Oct 09:15, written before it runs)
**Why.** The first fresh-grid cells (seed 2029, actuated) show E's delay against P0 (before the longer drive is charged) moving with the share of drivers who actually divert:

| Plan | Compliance | Share actually diverting | Delay against P0 |
|---|---|---|---|
| P2 | 0.3 | 3.3% | −4.9% |
| P2 | 0.5 | 5.5% | −5.0% |
| P1 | 0.3 | 30% | −22.0% |
| P1 | 0.5 | 50% | +18.9% |

So the Lead's capacity rule (spare 260 veh/h from the fixed-time sensitivity on replay-v2) may set the share far below what helps on this P0.

**What runs.** `data/generated-plans/IN-26-02615-data-share-0.2-oct15/` (`scripts/tuen_mun/share_sweep_plans.py`):
- the Lead's P0, P1 and generation inputs byte for byte, and the Lead's P2 with share 0.2, checked by D's validator;
- a diagnostic, not a Ripple plan.

**Cells.** Only the calibration seeds 2026–2028, so the share is chosen before any fresh seed:
- `p0x-merge-at-site{,-s2027,-s2028}` with actuated signals, and the new `p0x-merge-at-site-fixed{,-s2027,-s2028}` with fixed-time signals;
- compliance 0.3 and 0.7, the two ends of the tested range;
- P0 and P2 only: 24 runs into `results/tuen-mun-share-sweep-oct15/`, after Part D and before Part B.

**Plan-set name.** E's plan-set name is `data-share-020-oct15`: E allows only lower-case letters, digits and hyphens. The directory keeps its name.

**Two P0 results set aside.** Replay-v2's seed-2029 P0 runs at compliance 0.3 and 0.5 were set aside and will run again in their turn. Their scratch folders were deleted by mistake, and the comparison needs them. The first copies are kept outside `results/`, to check that the reruns match.

**What it decides.** Nothing. It informs the Lead's next plan generation. A share chosen from it still needs fresh seeds, beyond 2031, before it can be a candidate.

### Part E outcome (15 Oct 12:47)
Share 0.2 against P0 on the calibration seeds 2026–2028 (`results/tuen-mun-share-sweep-oct15/comparison_p0x-merge-at-site.txt`, longer drive charged):

| Signals | Cases better than P0 | Range | Median | Cars diverted |
|---|---|---|---|---|
| Actuated | 18 of 18 | −5.9% to −13.2% | −7.6% | 94–292 |
| Fixed-time | 15 of 18 | −7.9% to +5.4% | −5.0% | 88–235 |

The fixed-time case that loses is seed 2028 at compliance 0.3: +5.4 / +4.2 / +2.5%. Its P0 is the lowest of the six P0s (1,216 vehicle-hours with 4 min outside, against 1,234–1,308), and that P2 (1,267) is within the other cells' P2 range of 1,135–1,299. With one run per cell, seed-to-seed noise of about ±4% decides cells where the effect is small.

## Part F: share 0.2 on fresh seeds 2032–2034 (written before it runs)
**What runs.** Data's share 0.2 from Part E, the only share tried, on seeds 2032, 2033 and 2034. These were never used before (2029–2031 have now been seen).
- **Cells:** actuated and fixed-time signals, compliance 0.3, 0.5 and 0.7; P0 and P2 of `data/generated-plans/IN-26-02615-data-share-0.2-oct15` (plan-set name `data-share-020-oct15`).
- **Runs and folder:** 36 runs into `results/tuen-mun-share-020-fresh-oct15/`, then Part B.

**Decision rule, unchanged.** P2 lower than P0 in every cell and under 0, 4 and 10 outside minutes.

**Status of the result.** Data chose the share, not D, so even a win is a proposal for the Lead to generate through D and the 16 Oct review, not a Ripple plan.

### Part F outcome (15 Oct 15:05)
Share 0.2 on the fresh seeds 2032–2034 (`results/tuen-mun-share-020-fresh-oct15/comparison_p0x-merge-at-site.txt`; all 18 P0s meet version 2):

| Signals | Cases better than P0 | Range | Median |
|---|---|---|---|
| Actuated | 25 of 27 | −12.4% to +1.1% | −6.7% |
| Fixed-time | 24 of 27 | −7.4% to +4.8% | −4.2% |

**It does not pass the every-cell rule.** Two cells are worse than P0:
- actuated seed 2032 at 0.3: +1.1 / +0.5%;
- fixed-time seed 2032 at 0.5: +4.8 / +3.7 / +2.1%.

**Mean over three seeds, with 4 min charged outside** (a reading, not the rule):

| Signals | Compliance | Share 0.11 (seeds 2029–2031) | Share 0.2 (seeds 2032–2034) |
|---|---|---|---|
| Actuated | 0.3 | −2.1% | −4.2% |
| Actuated | 0.5 | −3.7% | −5.8% |
| Actuated | 0.7 | −6.3% | −9.3% |
| Fixed-time | 0.3 | −4.8% | −1.3% |
| Fixed-time | 0.5 | −3.3% | −1.7% |
| Fixed-time | 0.7 | −2.1% | −6.2% |
| All cells | | −3.7% (sd 2.5) | −4.8% (sd 4.0) |

The two shares ran on different seeds, so the two columns are not a matched comparison.

### Part B, stopped after two cells
Part B, the Lead's plan set on replay-v2, stopped after seed 2029 at compliance 0.3 and 0.5 (`results/tuen-mun-lead-grid-oct15/comparison_replay-v2.txt`). P2 is already worse than P0 in one of them (0.3: +0.9 / +0.4%), so replay-v2 cannot pass the every-cell rule either. Simulation rates that P0 no-go anyway.

The six runs' scratch folders were removed after the comparison was written. Their results and the comparison are kept.
