# Presentation Q&A Sheet & Claims Verification

## 1. Technical & Model Limitations (Data Freeze & Milestone Governance)

### Q1: Why are Delay Savings, CO2 Reduction, and Benefit-Cost Ratio (BCR) left blank?
> **Answer**: 
> Performance metrics remain strictly **BLANK / Not Measured Yet**. As noted in the 13 Oct Simulation Diagnostic ([`sim/lead-plans-diagnostic-oct13` at a48b8c9](https://github.com/f1ymango/ripple/commit/a48b8c9)), current P1/P2 simulation runs are unsuitable for public plan comparison due to closure-phase traffic deficits and entry-ramp sensitivity. No incident-specific delay, emissions, or benefit claims are made prior to post-freeze evidence sign-off.

### Q2: What is the current diagnostic status of AI-generated response plans (P1/P2) versus baseline (P0)?
> **Answer**: 
> The system provides a working incident-analysis prototype that generates and ranks candidate plans. However, current diagnostic evaluations show that P1 performs worse than P0, while P2 ties P0 (establishing no traffic benefit). Furthermore, P0 contains empty plan actions (no added advisory instructions), distinct from both the simulator's automatic closure rerouting and the Transport Department's (TD) later observed advice.

### Q3: What is the timeline and criteria for locking final presentation claims?
> **Answer**: 
> - **15 Oct**: Evidence & Export Checkpoint (Final Presentation Pack)
> - **16 Oct**: Provisional Claims Freeze
> - **17 Oct**: Internal Submission Target
> 
> Unless a source-supported P0 baseline passes joint Data/Simulation validation before the checkpoint, the 15 Oct presentation pack will strictly fallback to observed playback and working console workflow, omitting route recommendations and savings figures.

### Q4: What is the accuracy of the Reader Agent in parsing traffic incident reports?
> **Answer**: 
> The initial held-out all-fields-correct evaluation scored **50% citywide** (40/80) and **75% corridor** (15/20). After prompt and label corrections, the development evaluation scored **75% citywide** (60/80) and **85% corridor** (17/20; `results/reader/2026-09-25T0048_qwen3-8b_score.json`). A separate 1 Oct prompt experiment scored 62.5% and 60%. See `data/labelled_incidents/LABELLING.md`.

---

## 2. Methodology & Evidence Traceability

| Claim / Topic | Primary Source Artifact | Current Verification Status |
| :--- | :--- | :--- |
| **Lane-phase inference** | `results/data/closed-lanes_AID01104_20260515-0840_1010.md` | Detector-inferred initial lane/onset (physical phase remains assumed) |
| **Flow Balance Inputs** | `results/data/flow-balance_20260515-0755_0855.json` | Verified (Data Owner) |
| **Reader Parsing Score** | `results/reader/2026-09-25T0048_qwen3-8b_score.json` | Development score after prompt/label corrections (Reader Owner) |
| **13 Oct Root Cause Assessment** | `docs/component-c-validation-root-cause-2026-10-13.md` | Logged on branch `sim/lead-plans-diagnostic-oct13` at `a48b8c9` |
| **Incident-specific savings** | No accepted result set | **BLANK / Not Claimed** |

---

## 3. Stakeholder Interview & Evidence Readiness

### 1. Interview Evidence Scoping
- **Current Scope**: Qualitative evidence from **1 anonymous experienced green-minibus driver interview**.
- **Governance Requirement**: Qualitative only. Do not refer to this as a "verified domain-expert interview".

### 2. Missing Technical Artifacts Register (15 Oct Checkpoint Blockers)
- **E (Data)**: Result and provenance sidecars (`docs/03-architecture.md`).
- **Simulation**: Network setup, ramp behavior, and incident validation.
- **Visuals**: Final high-resolution console screenshots, reviewed video script, and video MP4 export matching `deck/video-shot-list.md`.
