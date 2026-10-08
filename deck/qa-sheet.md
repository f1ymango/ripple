# Presentation Q&A Sheet & Claims Verification

## 1. Technical & Model Limitations (Data Freeze Governance)

### Q1: Why are Delay Savings, CO2 Reduction, and Benefit-Cost Ratio (BCR) left blank?
> **Answer**: 
> The project adheres strictly to the **Oct 14 Data Freeze** governance rule. The current simulation artifacts in `results/twin/` reflect early pre-incident diagnostic runs (07:55–08:55) rather than validated full-closure runs. To avoid false or unverified claims, all delay-saving, environmental, and financial ratio metrics remain explicitly labeled as **`Not Measured Yet`** until full-closure simulation runs are completed and signed off before October 14.

### Q2: What is the accuracy of the Reader Agent in parsing traffic incident reports?
> **Answer**: 
> According to our Reader benchmark results (`results/reader/2026-10-01T190919941153_qwen3-8b_score.json`), the current Qwen3-8B model achieves a Gold Score v2 of **75% citywide accuracy** and **85% corridor accuracy**. Prompts and schemas continue to be refined to handle complex edge cases prior to final evaluation.

### Q3: How was the SUMO Digital Twin calibrated, and what is its current scope?
> **Answer**: 
> SUMO demand fitting and flow balancing are calibrated using real-world loop detector data (`results/data/flow-balance_20260515-0755_0855.json`). The current verified window covers the pre-incident period leading up to queue onset. Full incident propagation and lane closure replay are under active validation for the post-freeze release.

### Q4: Are the visual clips in the presentation fully validated against the May 15 incident?
> **Answer**: 
> No. Visual clips like `results/twin/aberdeen-diagnostic.gif` are early September diagnostic excerpts (run under SUMO 1.27.1) used strictly to demonstrate the simulator pipeline capabilities. They do not represent final validated outputs for the May 15 demo incident.

---

## 2. Methodology & Evidence Traceability

| Claim / Topic | Primary Source Artifact | Current Verification Status |
| :--- | :--- | :--- |
| **Observed Lane Closures** | `results/data/closed-lanes_AID01104_20260515-0840_1010.json` | Verified (Data Owner) |
| **Flow Balance Inputs** | `results/data/flow-balance_20260515-0755_0855.json` | Verified (Data Owner) |
| **Reader Parsing Score** | `results/reader/2026-10-01T190919941153_qwen3-8b_score.json` | Verified (Reader Owner) |
| **Pre-Incident Simulation** | `results/twin/may15-preincident-diagnostic.json` | Provisional (Simulation Owner) |
| **Full-Closure Savings** | N/A | **Pending Oct 14 Data Freeze** |
