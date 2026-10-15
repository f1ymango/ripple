# Two-incident demo pack (Data, 15 Oct 2026, for the 16 Oct cut)

**For:** Impact (deck, evidence pack) and Visuals (console, video).

**Pack:** `results/demo-oct16/`, built by `python scripts/demo_pack.py`. Every file is copied unchanged from where E and the ranking tool wrote it. The Lead's 11% Tuen Mun P2 is frozen: no further share or timing tuning.

## The story in two cases

| | Aberdeen (IN-26-03365, 15 May 2026) | Tuen Mun (IN-26-02615, 15 Apr 2026) |
|---|---|---|
| What happened | Crash on the Wong Chuk Hang Road flyover (Aberdeen Tunnel bound) near Yip Kan Street, morning peak; both lanes shut 09:00–10:00; the only way round is Wong Chuk Hang Road under it | Crash on Tuen Mun Road near Hong Kong Garden, evening peak; one or two of three lanes shut 17:48–18:47 |
| Ripple's plans | P1: send drivers round; P2: the Lead's coordinated detour (80%/70% shares plus a signal change at Tong Bin Lane) | P1: advise everyone to Tuen Mun via Castle Peak Road; P2: advise 11% of them |
| What the simulator found, over a grid of seeds and assumptions | P2 and doing nothing **tie**; sending drivers round is worse | P2 **beats** doing nothing and beats sending everyone round |
| What Ripple does | **Refuses to recommend.** The evidence does not support any plan over doing nothing. | **Recommends P2**, as a modelled candidate |
| Message | Ripple will not push a plan it cannot back | Targeted advice helps; telling everyone to divert makes things worse |

## Result card: Tuen Mun
**Modelled candidate, not a measured road saving.**

| | Doing nothing (P0) | Everyone advised (P1) | 11% advised (P2) |
|---|---|---|---|
| Simulated delay, the console's cell (compliance 50%, seed 2029) | 1,300.6 veh-h | 1,545.9 veh-h | **1,235.1 veh-h** |
| The same, including the longer Castle Peak Road drive (4 min per driver who switches to Route 3) | 1,300.6 | 1,585.4 (+21.9%) | **1,242.8 (−4.4%)** |
| Drivers on the longer route | 0 | 533 | 102 |

**Over all 18 cells**:
- the cells: fresh seeds 2029–2031 × compliance 30/50/70% × two signal designs at Sham Tseng;
- the ranking: P2 before P0 by **4.3%** of P0's delay (95% interval 3.0–5.6%), lower in 17 of 18 cells;
- with the longer drive charged, **3.7%** (2.4–5.0%);
- P1 is worse than P0 by 37% (20–55%).

**Sources:**
- `results/rankings/lead-capacity-oct15-p0x-merge-at-site.json`
- `results/tuen-mun-lead-grid-oct15-p0x-merge-at-site/comparison_p0x-merge-at-site.{json,txt}` (`scripts/tuen_mun/report.py`)

**Say:**
- "In our simulation of the 15 April Tuen Mun crash, advising about one in nine Tuen Mun-bound drivers to use Castle Peak Road cut total delay by about 4%."
- "Advising everyone made it 20–40% worse."

**Do not say:**
- that this was measured on the road;
- that it saves a stated number of hours in reality;
- "proven".

## Result card: Aberdeen
| | P0 | P1 | P2 |
|---|---|---|---|
| Simulated delay, the console's cell (compliance 50%, 66 min clearance, seed 2026) | 779.5 veh-h | 833.4 veh-h | 799.2 veh-h |

**Over 30 counting cells:**
- P0 and P2 tie: P2 is 1.4% lower, with a 95% interval from 4.1% lower to 1.2% higher.
- P0 is before P1 by 3.4%.
- **No plan beats both others, so the console withholds a recommendation and shows why.**

**Source:** `results/rankings/lead-draft-20261013-b.json`.

**Say:** "Ripple found no plan that reliably beats doing nothing, so it told the operator so."

## Simulation's final call (15 Oct, 20:34)
`docs/tuen-mun-simulation-final-call-2026-10-15.md` on `sim/tuen-mun-p0-variants-oct15` at 5ec8c1d. It uses this frozen 11% P2 pack and leaves the results unchanged:
- **Ready** for the frozen two-case presentation.
- **Not ready** for a measured traffic-improvement claim.
- **Agreed wording:** "modelled candidate ranked ahead", with the queue limitation visible.

**Caption for the video and slides** (keep it on screen with the Tuen Mun result):
> Modelled in SUMO for the 15 April 2026 crash. The model's queue moves faster than TD measured (about 42 vs 21 km/h), clears early and lets too much traffic through after the reopening, so this is a modelled estimate, not a measured saving.

## Limits to state in the technical evidence (not the centre of the video)
- **Tuen Mun's baseline (`p0x-merge-at-site`)** meets the team's validation targets on all 21 runs. But its queue between Sham Tseng and the crash moves faster than TD measured (about 42 against 21 km/h), it clears early, and after the reopening it discharges about 6,100 veh/h against TD's 4,560–4,900. A stress test with a slower, all-lanes queue still has P2 ahead of P0 in 6 of 6 cells (`docs/tuen-mun-stress-zipper-2026-10-15.md`, side branch `data/v3-dev`). That model breaks traffic flow past the crash, so it is not used as the baseline.
- **Two rule readings for Tuen Mun:**
  - the team's ranking rule favours P2;
  - the stricter Tuen Mun protocol rule (lower in every single cell) fails on one cell: +1.9% at 30% compliance, seed 2030.
  - Both are in `docs/tuen-mun-go-no-go-evidence-2026-10-15.md`.
- **Aberdeen's P2 signal change** at Tong Bin Lane is netconvert's guess, with no TD timing. Without it, doing nothing comes first (`results/rankings/lead-p2-nosignal-oct13.json`).

## Showing it in the console
The console shows one incident at a time, from the folders named in its environment. In PowerShell, from the repo:

```
$env:RIPPLE_RESULTS_DIR="results/demo-oct16/tuen-mun/runs"; $env:RIPPLE_PLANS_DIR="results/demo-oct16/tuen-mun/plans"; streamlit run src/console/app.py
$env:RIPPLE_RESULTS_DIR="results/demo-oct16/aberdeen/runs"; $env:RIPPLE_PLANS_DIR="results/demo-oct16/aberdeen/plans"; streamlit run src/console/app.py
```

**Checked headless** with Streamlit's AppTest, with no exceptions:
- **Tuen Mun:** "Recommended operator response: Capacity-bounded Castle Peak Road advice (P2). Lower simulated total delay than each other plan over a grid of 18 seeds and assumptions (95% confidence)."
- **Aberdeen:** "Recommendation unavailable: The plan set's ranking puts no plan before both others (P0 before P1; P0 and P2 tie; P2 before P1); no plan can be recommended."

**Gaps for Visuals and the Lead:**
- **The map is Aberdeen's.** The console's corridor map and incident playback are built for Aberdeen. With Tuen Mun loaded, the top map still shows the Aberdeen corridor, so film only the "Simulation plan comparison" panel for Tuen Mun, or use the result card above.
- **No approved Tuen Mun console briefing yet.** The console still says "The recommended run has no saved operator briefing yet" for this pack. The Lead has saved a provenance-bound F draft at `data/generated-briefings/IN-26-02615-p2-demo-oct16.json` for the single packed 50%-compliance, seed-2029 result. It awaits human bilingual/operator review and must not be presented as an approved instruction; its about −5% token is not the 18-condition −4.3% ranking.
- **The console's delay is E's delay.** The detour-inclusive figures are only in the result card above.
