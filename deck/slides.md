# Presentation Deck Draft (11 Oct evidence review)

---

## Slide 1: Problem & Real-World Impact
- **Urban Congestion Bottleneck**: Traffic incidents causing lane closures severely disrupt corridor flow and throughput.
- **Observed sources**: Archived TD messages (`data/demo_incident_messages.jsonl`) and detector readings inform the 15 May case. The initial slow-lane phase and physical onset are model assumptions inferred from AID01104, not confirmed TD closure times (`results/data/closed-lanes_AID01104_20260515-0840_1010.md`).
- **Traceability**: The flow-balance study and provisional simulation inputs identify their sources and assumptions (`results/data/flow-balance_20260515-0755_0855.json`).

---

## Slide 2: Technical Innovation (Reader & Digital Twin)
- **Incident Report Parsing**:
  - Powered by Qwen3-8B local LLM pipeline.
  - The corrected-prompt development evaluation scored **75% citywide** (60/80) and **85% corridor** (17/20) all-fields-correct (`results/reader/2026-09-25T0048_qwen3-8b_score.json`). These are not untouched held-out scores; the initial held-out evaluation scored 50% and 75%, respectively. The separate 1 Oct prompt experiment scored 62.5% and 60% and was not adopted.
- **Digital Twin Simulation (SUMO)**:
  - Microscopic flow balancing and pre-incident demand fitting (`results/twin/may15-preincident-diagnostic.json`).
  - An incident P0 replay and P1/P2 rehearsal runs exist as diagnostics on Data's [evaluator PR #55](https://github.com/f1ymango/ripple/pull/55). Data and Simulation do not accept them for public plan comparison by the 14 Oct freeze.

---

## Slide 3: System Architecture & Data Pipeline
- **Inputs to the twin**:
  - Archived TD prose is parsed by the Reader; detector archives are prepared separately by the data layer. The structured incident and observed detector inputs feed the bounded SUMO case.
- **Reproducibility & Evidence**:
  - Saved evaluation files and provenance sidecars identify the inputs behind diagnostic runs; the public demo distinguishes observed traffic from simulated and fixture-based screens.

---

## Slide 4: Feasibility & Financial Framework
- **Operational Cost Model**:
  - Local-model and SUMO operation are feasible prototype choices. A deployment cost requires a priced configuration and measured usage; no monthly cost is claimed yet.
- **Data Freeze Boundary Governance**:
  - **Delay savings**: no accepted incident-specific benefit claim
  - **CO₂ reduction**: no accepted incident-specific benefit claim
  - **Benefit-cost ratio (BCR)**: not calculated
  *The 14 Oct results freeze locks supported claims; it does not imply that outstanding validation will succeed.*

---

## Slide 5: Roadmaps & Immediate Next Steps
- **Oct 12**: Review the observed-data demo, draft video, deck and Q&A wording.
- **Oct 14**: Freeze accepted results and the claims they support.
- **Oct 17**: Internal submission target for the deck, prototype and video (official deadline: 18 Oct).
