# Tuen Mun: stress test of P2 against a P0 whose lanes all queue (15 Oct 2026, 16:05, written before it runs)

**Question:** does the Lead's P2 lead over P0 depend on the fault in `p0x-merge-at-site`? In that P0 the open lane, which is also the Sham Tseng exit lane, stands still while the shut lanes run on.

**Model.** Data's merging-in-turn rule, version 4. It is the `dev-v4a` configuration on this branch: `src/evaluator/simulate.py` sha256 a633f8368be9…, `--move-over approach --merge-in-turn --keep-lanes`, passing at 30 km/h. It was chosen on P0 behaviour alone, before any P2 run on it:

| Check (development seed 2040) | dev-v4a | TD |
|---|---|---|
| Lane-speed spread at TDS90025–31 | 20.2 km/h | 6.0 km/h |
| Queue speed at TDS90024–31, 18:00–18:45 | 23.6 km/h | 20.6 km/h |
| Wrong-lane teleports, other | 0 | |
| One-lane throughput past the site | about 1,270 veh/h | 1,584–1,740 veh/h |

The throughput shortfall makes it fail validation v2 (GEH about 81%). **It is not a P0**: it is a stress case for one question.

**Cells:**
- `stress-zip-s2026/2027/2028` (actuated signals) and `stress-zip-fixed-s2026/2027/2028` (fixed-time);
- compliance 0.5;
- the Lead's plan set `IN-26-02615-lead-capacity-oct15`, P0 and P2;
- 12 runs into `results/tuen-mun-stress-zipper-oct15/`.

**What is reported:** P2 against P0 per cell, with the longer drive charged (`scripts/tuen_mun/report.py`).

**How it is read, set now:**
- If P2 is lower than P0 in at least 5 of the 6 cells, with a negative mean, the merge-at-site result does not hinge on the stalled lane.
- Anything else means it might.

This feeds Simulation's decision on the P0. It is not a ranking and makes no claim.

## Outcome (15 Oct, 17:05)
`results/tuen-mun-stress-zipper-oct15/comparison_stress-zip.txt`. P0 numbers from `scripts/tuen_mun/p0_variants_report.py` functions; p0x-merge-at-site seed 2029 at compliance 0.5 for comparison.

| | TD | p0x-merge-at-site | Stress P0, 6 seeds |
|---|---|---|---|
| Queue speed at TDS90024–31, 18:00–18:45 | 20.6 km/h | 43.5 km/h | 19.6–24.9 km/h |
| Lane-speed spread | 6.0 km/h | 36.8 km/h | 17.7–21.0 km/h |
| Last congested bin at TDS90024 / TDS90029 | 19:25 / 18:45 | 18:45 / 18:35 | 18:45 / 18:45 |
| Discharge at TDS90033, 18:50–19:00 | 4,500–4,890 veh/h | 5,020–6,130 veh/h | 4,910–6,700 veh/h |
| One-lane throughput past the site, 18:00–18:15 | 1,584–1,740 veh/h | 1,556 veh/h | 1,264–1,272 veh/h, and **48–72** in 3 of 6 seeds |
| GEH | | 86.3% | **72.9–83.3%** (fails v2) |
| P0 delay | | 1,300.6 veh-h | 1,696–2,784 veh-h |

**The change: no.**
- **Queue:** it fixes the queue speed and most of the lane imbalance.
- **Recovery and discharge:** it does not fix recovery at Ting Kau or the discharge after the reopening.
- **Traffic flow:** it breaks the flow past the site. GEH fails, and in 3 of 6 seeds the merge nearly locks up for 10–15 minutes.

**P2's advantage: it survives.** P2 is lower than P0 in all 6 cells, under 0, 4 and 10 min outside (18 of 18).
- Actuated: −0.6% to −5.1%, median −4.3%.
- Fixed-time: −5.3% to −7.1%, median −6.1%.

By the reading set before the runs (at least 5 of 6, with a negative mean), the merge-at-site result does not hinge on the stalled open lane.

**Following the Lead's direction (15 Oct, 16:39):** this repair attempt stops. The current result (`p0x-merge-at-site`) is used, with its limitation stated.
