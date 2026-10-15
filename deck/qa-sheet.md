# Presentation Q&A Sheet & Claims Verification

## 1. Technical & Model Limitations (Data Freeze & Milestone Governance)

### Q1: Why are measured traffic savings and BCR left blank for the Aberdeen case, while Tuen Mun reports a percentage?
> **Answer**: 
> - **Aberdeen**: Performance metrics remain strictly **BLANK / Not Measured Yet**. Because both lanes shut at 09:00:30, all traffic was naturally forced onto Wong Chuk Hang Road. No rerouting plan could improve delay over P0.
> - **Tuen Mun**: The reported **-4.3% delay reduction** (or -3.7% with detour distance charged) is a **modeled simulation candidate** under a 11% capacity-bounded P2 plan. It is presented as a prototype simulation result, not a measured real-world road saving.

### Q2: What is the current diagnostic status of AI-generated response plans (P1/P2) versus baseline (P0)?
> **Answer**: 
> - **Aberdeen**: P1/P2 tie or perform worse than P0 when unsourced signal changes are removed. Ripple's console correctly refuses to recommend unsupported advice.
> - **Tuen Mun**: Unrestricted broadcast (P1) causes severe spillover (+37% delay), whereas targeted 11% advice (P2) ranks ahead of P0 in 18 tested simulation conditions (-4.3%, 95% CI -5.6 to -3.0).

### Q3: What is the timeline and criteria for locking final presentation claims?
> **Answer**: 
> - **15 Oct**: Evidence & Export Checkpoint (Two-Incident Demo Pack Freeze)
> - **16 Oct**: Provisional Claims Freeze & Go/No-Go Decision
> - **17 Oct**: Internal Submission Target

### Q4: What is the accuracy of the Reader Agent in parsing traffic incident reports?
> **Answer**: 
> Development evaluation scored **75% citywide** (60/80) and **85% corridor** (17/20; `results/reader/2026-09-25T0048_qwen3-8b_score.json`). Held-out baseline scored 50% citywide and 75% corridor. See `data/labelled_incidents/LABELLING.md`.

---

## 2. Two-Incident Presentation Strategy Summary

| Incident | Case Type | Core Pitch Narrative | Key Evidence / Metric |
| :--- | :--- | :--- | :--- |
| **Aberdeen (15 May)** | Observed / Safety Refusal | "Honest Co-pilot": Detects closure 35 min ahead of official broadcast; refuses unproven advice when P0 is optimal. | 35-min detection gap; Delay savings strictly **BLANK** |
| **Tuen Mun (15 Apr)** | Simulated / Positive Prototype | "Targeted Control": Capacity-bounded P2 (11% detour) beats P0 and avoids P1's gridlock. | **-4.3%** modeled delay reduction (simulated candidate) |

---

## 3. Stakeholder Interview & Evidence Readiness

### 1. Interview Evidence Scoping
- **Current Scope**: Qualitative evidence from **1 anonymous experienced green-minibus driver interview**.
- **Governance Requirement**: Qualitative only. Do not refer to this as a "verified domain-expert interview".

### 2. Missing Technical Artifacts Register (15 Oct Checkpoint)
- **E (Data)**: Demo pack updated under `results/demo-oct16/`.
- **Simulation**: Baseline P0 queue limitations documented in `docs/demo-two-incidents-2026-10-16.md`.
- **Visuals**: Two-case storyboard in progress using Aberdeen refusal + Tuen Mun result card.
