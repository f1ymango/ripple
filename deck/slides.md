# Presentation Deck Draft (Reviewable Oct 12 Version)

---

## Slide 1: Problem & Real-World Impact
- **Urban Congestion Bottleneck**: Traffic incidents causing lane closures severely disrupt corridor flow and throughput.
- **Data-Driven Verification**: Leveraging real incident logs (`results/data/closed-lanes_AID01104_20260515-0840_1010.json`) and flow balance records (`results/data/flow-balance_20260515-0755_0855.json`) to establish precise baseline conditions.
- **Traceability Guarantee**: All incident parameters mapped directly to verifiable hub artifacts.

---

## Slide 2: Technical Innovation (Reader & Digital Twin)
- **Incident Report Parsing**:
  - Powered by Qwen3-8B local LLM pipeline.
  - Achieves **75% citywide** and **85% corridor** parsing accuracy (Gold Score v2, verified in `results/reader/2026-10-01T190919941153_qwen3-8b_score.json`).
- **Digital Twin Simulation (SUMO)**:
  - Microscopic flow balancing and pre-incident demand fitting (`results/twin/may15-preincident-diagnostic.json`).
  - Diagnostic replay framework established for event-driven traffic analysis.

---

## Slide 3: System Architecture & Data Pipeline
- **End-to-End Pipeline**:
  - `Raw Unstructured Logs` $\rightarrow$ `Reader Parsing Agent` $\rightarrow$ `Flow-Balance Engine` $\rightarrow$ `SUMO Micro-Simulation`.
- **Reproducibility & Evidence**:
  - Every calculation, script execution, and scoring output committed under strict GitHub workflow traceability.

---

## Slide 4: Feasibility & Financial Framework
- **Operational Cost Model**:
  - Infrastructure footprint estimated at **~\$300 – \$600 / month** (LLM local execution + Cloud VM SUMO nodes).
- **Data Freeze Boundary Governance**:
  - **Delay Savings**: `BLANK / Not Measured Yet`
  - **CO2 Reduction Benefits**: `BLANK / Not Measured Yet`
  - **Benefit-Cost Ratio (BCR)**: `BLANK / Not Measured Yet`
  *Note: Quantitative return metrics strictly reserved until post-freeze full-closure simulation sign-off (Oct 14).*

---

## Slide 5: Roadmaps & Immediate Next Steps
- **Oct 12**: Reviewable Draft PR freeze & QA sheet alignment (Current Stage).
- **Oct 14**: Final Data Freeze & execution of full-closure SUMO simulation runs.
- **Oct 15**: Submission of fully-validated metrics, BCR, and final presentation package.
