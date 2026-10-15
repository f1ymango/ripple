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
