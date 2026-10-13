# Presentation Q&A Sheet & Claims Verification

## 1. Technical & Model Limitations (Data Freeze Governance)

### Q1: Why are Delay Savings, CO2 Reduction, and Benefit-Cost Ratio (BCR) left blank?
> **Answer**: 
> The provisional 16 Oct results freeze (Lead update, 13 Oct) locks the evidence used in the submission. Data's incident P0 replay and P1/P2 rehearsal runs were integrated through [PR #61](https://github.com/f1ymango/ripple/pull/61), but Data and Simulation jointly find them unsuitable for public plan comparison. In particular, the plan effect changes with a disputed ramp representation. We therefore make no incident-specific delay, emissions or benefit-cost claim. The freeze does not guarantee validation.

### Q2: What is the accuracy of the Reader Agent in parsing traffic incident reports?
> **Answer**: 
> The initial held-out all-fields-correct evaluation scored **50% citywide** (40/80) and **75% corridor** (15/20). After prompt and label corrections, the development evaluation scored **75% citywide** (60/80) and **85% corridor** (17/20; `results/reader/2026-09-25T0048_qwen3-8b_score.json`). Those latter figures are not a fresh held-out score. A separate, unadopted 1 Oct prompt experiment scored 62.5% and 60% (`results/reader/2026-10-01T190919941153_qwen3-8b_score.json`). See `data/labelled_incidents/LABELLING.md` for the score history.

### Q3: How was the SUMO Digital Twin calibrated, and what is its current scope?
> **Answer**: 
> Demand fitting uses archived detector counts (`results/data/flow-balance_20260515-0755_0855.json`). The corrected incident P0 replay on PR #55 scores 89.45% GEH<5 and 14.44% speed MAPE over the whole run, but closure-phase counts, tunnel-side flow, queue timing, speed inputs, ramp behaviour and wrong-lane teleports prevent acceptance for comparing plans. The scores describe a model diagnostic, not validated plan benefits. See [Data and Simulation's joint review](https://github.com/f1ymango/ripple/blob/a8d04aa/docs/evaluator-p0-go-no-go-2026-10-09.md).

### Q4: Are the visual clips in the presentation fully validated against the May 15 incident?
> **Answer**: 
> No. Visual clips like `results/twin/aberdeen-diagnostic.gif` are early September diagnostic excerpts (run under SUMO 1.27.1) used strictly to demonstrate the simulator pipeline capabilities. They do not represent final validated outputs for the May 15 demo incident.

---

## 2. Methodology & Evidence Traceability

| Claim / Topic | Primary Source Artifact | Current Verification Status |
| :--- | :--- | :--- |
| **Lane-phase inference** | `results/data/closed-lanes_AID01104_20260515-0840_1010.md`; `data/demo_incident_messages.jsonl` | Detector-inferred initial lane/onset and observed TD report times; physical phase remains assumed |
| **Flow Balance Inputs** | `results/data/flow-balance_20260515-0755_0855.json` | Verified (Data Owner) |
| **Reader Parsing Score** | `results/reader/2026-09-25T0048_qwen3-8b_score.json`; `data/labelled_incidents/LABELLING.md` | Development score after prompt/label corrections (Reader Owner) |
| **Incident P0 diagnostic** | [PR #55 P0 review](https://github.com/f1ymango/ripple/blob/a8d04aa/docs/evaluator-p0-go-no-go-2026-10-09.md) and its linked generated results | Joint Data/Simulation NO-GO for public plan comparison |
| **Incident-specific savings** | No accepted result set | No public claim at the provisional 16 Oct freeze unless the stated acceptance conditions are met |

---

## 3. Stakeholder Interview & Evidence Readiness

### 1. Interview Evidence Scoping
- **Current Scope**: Qualitative evidence from **1 anonymous experienced green-minibus driver interview**.
- **Governance Requirement**: Qualitative only. Do not refer to this as a "verified domain-expert interview" without separate independent verification.

### 2. Missing Technical Artifacts Register (10/15 PR Blockers)
To achieve full closure for the Oct 15 presentation pack, the following technical deliverables remain pending external owner sign-off:
- **E (Data)**: Result and provenance sidecars produced under `docs/03-architecture.md`, including accepted incident P0 baseline and full-closure P1/P2 simulation results under `results/`. (Required for Delay Savings, CO₂ Impact, and BCR calculation).
- **Simulation**: Network setup and incident validation (note: sidecar production is owned by E/Data, not Simulation).
- **Visuals**: Final high-resolution console screenshots, reviewed video script, and final video MP4 export matching `deck/video-shot-list.md`.

*Lead update, 13 Oct: deliver the 15 Oct evidence pack with the evidence then
available; it need not wait for accepted simulation benefits. The provisional
16 Oct freeze permits a reviewed final delta. Retain the observed-demo scope
and label GenAI draft/fixture demonstrations. If incident P0/P1/P2 remain
unaccepted, omit their benefit claims from the final deck.*
