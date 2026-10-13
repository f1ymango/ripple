# Real Incident vs. Simulated Baseline

## 1. Scope & Status Inventory (Lead decision 9 Oct; GenAI update 13 Oct)

| Item / Metric | Category | Source Artifact / Commit | Owner | Status / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **TD messages and detector inputs** | Observed, with lane-phase inference labelled | `data/demo_incident_messages.jsonl`<br>`results/data/closed-lanes_AID01104_20260515-0840_1010.md`<br>`results/data/flow-balance_20260515-0755_0855.json` | Data | TD report times are observed. The initial slow lane and 08:55 physical onset are inferred or assumed for the model. |
| **Reader Parsing & Verification** | Archived-message model output | `results/reader/2026-09-25T0048_qwen3-8b_score.json`<br>`data/labelled_incidents/LABELLING.md` | Lead (Reader) | Development all-fields-correct score after prompt/label corrections: 75% citywide, 85% corridor; initial held-out score: 50%, 75%. The 1 Oct experiment was not adopted. |
| **No-closure SUMO diagnostic** | Provisional simulation | `results/twin/may15-preincident-diagnostic.json`<br>`results/twin/oct05-flow-balance-independent.json` | Simulation | Independent count-fit review, not incident or plan validation. |
| **Incident P0 and rehearsal P1/P2** | Provisional simulation | [Joint review](../docs/evaluator-p0-go-no-go-2026-10-09.md)<br>`results/evaluator-rehearsal/` integrated through PR #61 | Data (E), Simulation (review) | Corrected replay is an internal diagnostic. The dated joint NO-GO remains in force despite the schedule extension. Rehearsal plans are not the new Lead-generated plans. |
| **Simulation Playback Excerpt (GIF)** | Visual / Diagnostic | `results/twin/aberdeen-diagnostic.gif` | f1ymango (Simulation) | **Diagnostic Excerpt Only** (Early Sept IN-26-06481 run under SUMO 1.27.1; *not* validated May demo incident) |
| **Delay-saving claims** | Public claim | No accepted comparable incident results | Lead | Omitted. Diagnostic model differences are not established road benefits. |
| **Generated candidate plans** | Retrospective GenAI draft | `data/generated-plans/IN-26-03365-lead-draft-20261013-b/` | Lead | Real Qwen3:8b output; constraints and E action mapping passed. Not simulated or approved; context includes later-known facts and assumed controls. |
| **Bilingual model briefing** | Failed fixture-model exercise | `evidence/ai-log/2026-10-13.jsonl` | Lead | Bounded real calls failed validation; no accepted F output. Existing mock workflow is not a newly generated real-incident briefing. |
| **CO₂ / travel-time benefits** | Public claim | No accepted comparable incident results | Lead | Omitted. |
| **Benefit-cost ratio** | Financial claim | No sourced deployment cost or accepted benefits | Impact | Not calculated. |

---

## 2. Known Limitations & Rules

- **Traceability**: Every number traces to an explicit artifact in `results/` or a cited source with its check date.
- **Results freeze**: Lead's 13 Oct update provisionally targets 16 Oct, with the 15 Oct pack checkpoint retained. Lock only figures supported by accepted evidence. Do not claim benefits from no-closure count scores or the unaccepted incident rehearsal.
- **Visuals Constraints**: Visualizations may utilize real incident playback and working console interfaces, but must **not** promise recommended-route highlights or evaluated-vehicle animations until validated.
- **Omitted Metrics**: Delay-saving, CO2-saving, travel-time benefit and
  route-recommendation claims remain omitted unless the complete multi-owner
  [acceptance gates](../docs/04-plan.md) are met before the provisional 16 Oct freeze. A
  full-closure result alone is insufficient.
