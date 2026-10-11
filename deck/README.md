# Ripple: Urban Corridor Traffic Simulation & AI Twin

This repository contains the simulation framework, AI agent pipelines, presentation materials, and technical evaluation suites for the Ripple urban corridor management project.

---

## 1. Executive Summary & Component Ownership

| Component Domain | Lead Owner | Current Scope & Responsibilities | Current Status |
| :--- | :--- | :--- | :--- |
| **Problem & Framing** | Impact / Pitch | Deck narrative, 5-criteria framing, ethics & costing governance | **Deployed 10/12 Reviewable Draft (#50)** |
| **Simulation & Twin** | Simulation | Network setup & incident AID01104 validation | Operational baseline verified |
| **Data & Provenance** | E (Data) | Result/provenance sidecars (`docs/03-architecture.md`) & `results/` artifacts | Diagnostic P0 review complete ([PR #55](https://github.com/f1ymango/ripple/pull/55)) |
| **Technical / GenAI** | Technical Lead | Qwen3-8B Reader benchmarks: 1 Oct (62.5% city / 60% corridor), Held-out (50%/75%), Dev run (75%/85%) | Score history logged in `LABELLING.md` |
| **Costing & Impact** | Impact / Pitch | Infrastructure cost model drafted; BCR set to `BLANK / Not Measured Yet` | Awaiting 10/14 freeze data |
| **Visuals & Media** | Visuals | Video shot list, storyboard, console screenshots, video exports | Storyboard ready (`deck/video-shot-list.md`) |

---

## 2. Activity & Change Log

- **2026-10-12**: Merged PR #50 (deck/ draft review pack). Scoped qualitative single-driver interview evidence, cost models (BCR blank), and exact Reader benchmark score history (1 Oct experiment vs held-out vs 25 Sep dev run).
- **2026-10-09**: Lead baseline decision locked; SUMO window and reader pipeline scope defined.
- **2026-10-03**: Submitted interim project report.

---

## 3. Repository Structure & Presentation Deliverables

All presentation materials and supporting evidence live under the [`deck/`](./deck/) directory:

- **[`deck/slides.md`](./deck/slides.md)**: 5-slide presentation deck covering all scoring criteria.
- **[`deck/costing.md`](./deck/costing.md)**: Infrastructure costing model (BCR strictly blank pending freeze).
- **[`deck/qa-sheet.md`](./deck/qa-sheet.md)**: Technical Q&A, Reader bounds, exact benchmark provenance, and single-driver qualitative interview evidence scope.
- **[`deck/real-vs-simulated.md`](./deck/real-vs-simulated.md)**: Real incident vs. SUMO twin mapping.
- **[`deck/video-shot-list.md`](./deck/video-shot-list.md)**: Storyboard and voiceover script for demo video.

---

## 4. Governance & Data Freeze Rules

1. **Oct 14 Data Freeze**: All metrics on delay savings, CO₂ impact, and Benefit-Cost Ratio (BCR) remain explicitly **`BLANK / Not Measured Yet`** across all deck documentation until post-freeze full-closure sign-off.
2. **Artifact Provenance**: Every quantitative claim must reference a verified file under `results/` produced and signed off by the respective owner.
