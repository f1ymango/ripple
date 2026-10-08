# Real Incident vs. Simulated Baseline

## 1. Scope & Status Inventory (Lead Decision Pending Oct 9)

| Item / Metric | Category | Source Artifact / Commit | Owner | Status / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Flow-balance Inputs & Closed-lane Rule** | Observed | `results/data/closed-lanes_AID01104_20260515-0840_1010.json`<br>`results/data/flow-balance_20260515-0755_0855.json` | Kandodaki (Data) | **Working** (May 15 demo window candidate evidence & flow balance) |
| **Reader Parsing & Verification** | Observed | `results/reader/2026-10-01T190919941153_qwen3-8b.jsonl`<br>`results/reader/2026-10-01T190919941153_qwen3-8b_score.json` | f1ymango (Reader) | **Working** (Gold Score v2: 75% citywide, 85% corridor accuracy) |
| **Pre-Incident SUMO Diagnostic** | Provisional Simulation | `results/twin/may15-preincident-diagnostic.json`<br>`results/twin/oct05-flow-balance-independent.json` | f1ymango (Simulation) | **Provisional** (07:55–08:55 pre-incident interval ending at queue onset) |
| **Simulation Playback Excerpt (GIF)** | Visual / Diagnostic | `results/twin/aberdeen-diagnostic.gif` | f1ymango (Simulation) | **Diagnostic Excerpt Only** (Early Sept IN-26-06481 run under SUMO 1.27.1; *not* validated May demo incident) |
| **Delay-Saving Claims** | Provisional Simulation | `-` | Simulation | **BLANK / Not Measured Yet** |
| **CO2 / Travel-Time Benefits** | Provisional Simulation | `-` | Data | **BLANK / Not Measured Yet** |
| **Benefit-Cost Ratio** | Costing | `-` | Lead | **BLANK / Not Measured Yet** |

---

## 2. Known Limitations & Rules

- **Traceability**: Every number traces to an explicit artifact in `results/` or a cited source with its check date.
- **Data Freeze Boundary**: Figures not measured prior to the Oct 14 data freeze must remain explicitly labeled as **"not measured yet"**. Do not compute delay savings or benefit-cost ratios from partial or no-closure count scores alone.
- **Visuals Constraints**: Visualizations may utilize real incident playback and working console interfaces, but must **not** promise recommended-route highlights or evaluated-vehicle animations until validated.
- **Omitted Metrics**: Delay-saving, CO2-saving, travel-time benefit, and route-recommendation claims are strictly omitted unless full-closure results are accepted before the Oct 14 freeze.
