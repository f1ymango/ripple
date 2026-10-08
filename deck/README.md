# Ripple: Urban Corridor Traffic Simulation & AI Twin

This repository contains the simulation framework, AI agent pipelines, presentation materials, and technical evaluation suites for the Ripple urban corridor management project.

---

## 1. Executive Summary & Component Ownership

| Component Domain | Lead Owner | Current Status & Scope |
| :--- | :--- | :--- |
| **Problem & Framing** | Impact / Pitch | **Deployed 10/12 Reviewable Draft (#50)** \| Frame & governance locked |
| **Simulation & Twin** | Simulation | Incident AID01104 replay & SUMO network window verified |
| **Technical / GenAI** | Technical Lead | Qwen3-8B Reader benchmarks: 75% City / 85% Corridor accuracy |
| **Costing & Impact** | Impact / Pitch | Infrastructure model drafted; BCR set to `BLANK / Not Measured Yet` |
| **Visuals & Media** | Visuals | Video shot list & storyboard ready (`deck/video-shot-list.md`) |

---

## 2. Activity & Change Log

- **2026-10-12**: Merged PR #50 (deck/ draft review pack). Fully scoped single interview evidence, cost models (BCR blank), and artifact dependency register for Oct 15 presentation pack.
- **2026-10-09**: Lead baseline decision locked; SUMO window and reader pipeline scope defined.
- **2026-10-03**: Submitted interim project report.

---

## 3. Repository Structure & Presentation Deliverables

All presentation materials and supporting evidence live under the [`deck/`](./deck/) directory:

- **[`deck/slides.md`](./deck/slides.md)**: 5-slide presentation deck covering all scoring criteria.
- **[`deck/costing.md`](./deck/costing.md)**: Infrastructure costing model (BCR strictly blank pending freeze).
- **[`deck/qa-sheet.md`](./deck/qa-sheet.md)**: Technical Q&A, Reader bounds, and anonymized interview evidence scope.
- **[`deck/real-vs-simulated.md`](./deck/real-vs-simulated.md)**: Real incident vs. SUMO twin mapping.
- **[`deck/video-shot-list.md`](./deck/video-shot-list.md)**: Storyboard and voiceover script for demo video.

---

## 4. Governance & Data Freeze Rules

1. **Oct 14 Data Freeze**: All metrics on delay savings, CO₂ impact, and Benefit-Cost Ratio (BCR) remain explicitly **`BLANK / Not Measured Yet`** across all deck documentation until post-freeze full-closure sign-off.
2. **Artifact Provenance**: Every quantitative claim must reference a verified file under `results/`.

> **Governance Note**: All delay savings, CO2 impact calculations, and Benefit-Cost Ratios (BCR) remain explicitly marked as **`BLANK / Not Measured Yet`** across all deck files until post-freeze full-closure simulation sign-off on Oct 14.
