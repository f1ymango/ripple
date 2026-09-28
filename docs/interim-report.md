# Interim Report Skeleton — Project Ripple

> **Internal submission target:** Saturday 3 October 2026
>
> **Official deadline:** Sunday 4 October 2026

Impact coordinates the report and collects a short, evidence-backed contribution from each component owner. This is an outline, not a claim that the work below is already complete. Any unmeasured result must be labelled as such.

## 1. Executive Summary & Social Problem

- **Owner:** Impact
- **Starting sources:** `docs/00-brief.md` §2 and `docs/05-pitch.md` §§1, 3.
- Explain the Hong Kong incident-response problem and why the Aberdeen corridor is the initial scope.
- Explain the limits of individual routing advice and the social and economic effects of disruption, using sourced claims.

## 2. Data, Incident Reader & System Architecture

- **Owner:** Lead; Data contributes the data-ingestion paragraph.
- **Starting sources:** `docs/02-data.md`, `docs/03-architecture.md` §1, and `docs/00-brief.md` §4.
- Describe the data feeds and their limits (A, Data), incident parsing (B, Lead), candidate plans and validation (D, Lead), briefing (F, Lead), and how a human operator approves advice.
- Show the pipeline and contracts without implying that the LLM computes simulation metrics.

## 3. Simulation, Evaluation & Preliminary Results

- **Owner:** Simulation; Data contributes evaluator methodology and results when available.
- **Starting sources:** `docs/03-architecture.md` §4 and `docs/00-brief.md` §6; use actual run artifacts in `results/` for all figures.
- Describe the SUMO corridor twin (C), calibration against observed detector data, and baseline-versus-plan comparison (E).
- State validation errors and scenario outcomes only from reproducible runs in `results/`; mark pending figures *not measured yet*.

## 4. Operator Console & Demo Visuals

- **Owner:** Visuals
- **Starting sources:** `docs/00-brief.md` §4 (G), `src/console/`, and the current map screenshot in `docs/img/`.
- Show the current console (G) and identify which map, playback, plan-comparison, and approval features are implemented versus planned.
- Include a screenshot or video link only when the corresponding artifact exists.

## 5. Feasibility, Sustainability, Ethics & Impact

- **Owner:** Impact
- **Starting sources:** `docs/05-pitch.md` §§5–6 and `evidence/interviews/2026-09-26-minibus-driver.md` (one qualitative interview).
- Present the single-corridor rollout costing and benefit-cost framework, with assumptions and sources.
- Summarise interview evidence as qualitative, including the number and profile of participants; avoid treating one interview as representative.
- Discuss spillover, privacy, and the limits of the current evidence.
