# Real Incident vs. Simulated Baseline

## 1. Scope & Status Inventory (Lead Decision Pending Oct 9)

| Item / Metric | Category | Source Artifact / Commit | Owner | Status / Notes |
| :--- | :--- | :--- | :--- | :--- |
| Flow-balance Inputs & Closed-lane Rule | Observed | `results/data/` | Data | Working |
| Reader Run Evidence & Interim Progress | Observed | `results/reader/` | Data / Sim | Working |
| SUMO Decision & Replay Evidence | Provisional Simulation | `results/twin/` | Simulation | Working / Provisional |
| Delay-Saving Claims | Provisional Simulation | - | Simulation | **BLANK / Not Measured Yet** |
| CO2 / Travel-Time Benefits | Provisional Simulation | - | Data | **BLANK / Not Measured Yet** |

## 2. Known Limitations & Rules
- Every number traces to a file in `results/` or to a cited source with the date it was checked.
- If a figure is not measured yet, write "not measured yet". Do not calculate delay savings or benefit-cost ratio from reproducible no-closure count score alone.
- Delay-saving and route-recommendation metrics are omitted unless accepted before Oct 14 data freeze.
