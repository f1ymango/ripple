# Presentation Q&A Sheet & Claims Verification

## 1. Technical & Model Limitations (Data Freeze Governance)

### Q1: Why are Delay Savings, CO2 Reduction, and Benefit-Cost Ratio (BCR) left blank?
> **Answer**: 
> The 14 Oct results freeze locks the evidence used in the submission. Data and Simulation jointly find current P1/P2 runs unsuitable for public plan comparison due to traffic boundary discrepancies and ramp modeling sensitivity. We therefore make no incident-specific delay, emissions, or benefit-cost claim. The freeze strictly enforces no unvalidated performance claims.

### Q2: What is the current status of AI-generated response plans (P1/P2) versus baseline (P0)?
> **Answer**: 
> As of 13 Oct diagnostic evaluations, the system successfully generates and ranks candidate plans through the evaluator pipeline. However, current diagnostic runs show P0 (which already incorporates observed Transport Department controls) outperforming or matching P1/P2. Furthermore, model sensitivity at the north-ramp entry changes P2 from added delay to savings. We present this as a functional incident-analysis workflow prototype, not a proven traffic-benefit system.

### Q3: What caused the validation discrepancies during closure phase diagnostics?
> **Answer**: 
> Root-cause assessment on 13 Oct identified missing or misplaced tunnel-bound traffic during incident closure (e.g., AID01106 recorded 89.5 veh/5min vs 46.6 simulated; AID01108 recorded 95.7 vs 46.2). The next defensible fix requires verified detector placement and turning counts before re-running P0/P1/P2.

### Q4: What is the accuracy of the Reader Agent in parsing traffic incident reports?
> **Answer**: 
> The initial held-out all-fields-correct evaluation scored **50% citywide** (40/80) and **75% corridor** (15/20). After prompt and label corrections, the development evaluation scored **75% citywide** (60/80) and **85% corridor** (17/20; `results/reader/2026-09-25T0048_qwen3-8b_score.json`). A separate 1 Oct prompt experiment scored 62.5% and 60%. See `data/labelled_incidents/LABELLING.md`.

---

## 2. Methodology & Evidence Traceability

| Claim / Topic | Primary Source Artifact | Current Verification Status |
| :--- | :--- | :--- |
| **Lane-phase inference** | `results/data/closed-lanes_AID01104_20260515-0840_1010.md` | Detector-inferred initial lane/onset |
| **Flow Balance Inputs** | `results/data/flow-balance_20260515-0755_0855.json` | Verified (Data Owner) |
| **Reader Parsing Score** | `results/reader/2026-09-25T0048_qwen3-8b_score.json` | Development score after prompt/label corrections |
| **13 Oct Root Cause Assessment** | `docs/component-c-validation-root-cause-2026-10-13.md` | Logged diagnostic bounds (Arivan/Sim) |
| **Incident-specific savings** | No accepted result set | **BLANK / Not Claimed** |

---

## 3. Stakeholder Interview & Evidence Readiness

### 1. Interview Evidence Scoping
- **Current Scope**: Qualitative evidence from **1 anonymous experienced green-minibus driver interview**.
- **Governance Requirement**: Qualitative only. Do not refer to this as a "verified domain-expert interview".

### 2. Missing Technical Artifacts Register
- **E (Data)**: Result and provenance sidecars (`docs/03-architecture.md`).
- **Simulation**: Network setup and incident validation.
- **Visuals**: Console screenshots, video script, and MP4 export matching `deck/video-shot-list.md`.
