# Observed Evidence vs. Modelled Comparisons

## 1. Scope & Status Inventory (16 Oct two-case claim boundary)

Mark's [two-case slide draft](slides.md) uses archived observations and saved
simulator comparisons for different purposes. The [evidence pack](../docs/demo-two-incidents-2026-10-16.md)
and [Simulation's final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md)
are the current sources for public wording; older rehearsals remain historical.

| Item / Metric | Category | Source Artifact / Commit | Owner | Status / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **TD messages and detector inputs** | Observed, with lane-phase inference labelled | `data/demo_incident_messages.jsonl`<br>`results/data/closed-lanes_AID01104_20260515-0840_1010.md`<br>`results/data/flow-balance_20260515-0755_0855.json` | Data | TD report times are observed. The initial slow lane and 08:55 physical onset are inferred or assumed for the model. |
| **Reader Parsing & Verification** | Archived-message model output | `results/reader/2026-09-25T0048_qwen3-8b_score.json`<br>`data/labelled_incidents/LABELLING.md` | Lead (Reader) | Development all-fields-correct score after prompt/label corrections: 75% citywide, 85% corridor; initial held-out score: 50%, 75%. The 1 Oct experiment was not adopted. |
| **No-closure SUMO diagnostic** | Provisional simulation | `results/twin/may15-preincident-diagnostic.json`<br>`results/twin/oct05-flow-balance-independent.json` | Simulation | Independent count-fit review, not incident or plan validation. |
| **Earlier incident rehearsal** | Historical diagnostic simulation | [Joint review](../docs/evaluator-p0-go-no-go-2026-10-09.md)<br>`results/evaluator-rehearsal/` integrated through PR #61 | Data (E), Simulation (review) | Not the frozen two-case comparison; do not source the slide result from these runs. |
| **Aberdeen P0/P1/P2** | Saved modelled comparison | [`results/demo-oct16/aberdeen/`](../results/demo-oct16/aberdeen/)<br>[incident review](../docs/incident-p0-verdict-2026-10-14.md) | Data (E), Simulation (review) | P0 and P2 tie under the team's ranking rule; the console withholds a recommendation. This is not proof that P0 is optimal or that no real intervention could help. The unsourced signal issue was found by human source review, not automatically by E. |
| **Tuen Mun P0/P1/P2** | Saved modelled candidate comparison | [`results/demo-oct16/tuen-mun/`](../results/demo-oct16/tuen-mun/)<br>[final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md) | Data (E), Simulation (review) | Frozen 11% P2 ranks ahead of P0 and P1 under the team's rule across 18 scored conditions: E delay −4.3% vs P0 (95% interval −5.6 to −3.0); blanket P1 +37.3%. P2 does not win every cell. Queue speed/recovery remain mismatched, so this is not a measured road saving. |
| **Simulation Playback Excerpt (GIF)** | Visual / Diagnostic | `results/twin/aberdeen-diagnostic.gif` | f1ymango (Simulation) | **Diagnostic Excerpt Only** (Early Sept IN-26-06481 run under SUMO 1.27.1; *not* validated May demo incident) |
| **Delay comparison versus road saving** | Public claim boundary | [Two-case result cards](../docs/demo-two-incidents-2026-10-16.md) | Lead + Impact | A labelled Tuen Mun **modelled** −4.3% E-delay comparison may be shown. Actual road savings are unmeasured; Aberdeen has no claimed saving. |
| **Generated candidate plans** | Recorded GenAI draft plus deterministic Lead bound | [Aberdeen drafts](../data/generated-plans/IN-26-03365-lead-draft-20261013-b/)<br>[Tuen Mun frozen plans](../data/generated-plans/IN-26-02615-lead-capacity-oct15/) | Lead | D drafted options; the Lead capacity rule capped Tuen Mun P2 from 80% to 11% before fresh-seed evaluation. Do not say the AI discovered the 11% share or calculated benefits. |
| **Bilingual operator briefing** | Provenance-bound single-cell draft | [`data/generated-briefings/IN-26-02615-p2-demo-oct16.json`](../data/generated-briefings/IN-26-02615-p2-demo-oct16.json) | Lead | F's Tuen Mun draft is bound to one packed run, not the 18-cell ranking. Human language/operator review is pending; it is not approved advice. |
| **CO₂ / travel-time benefits** | Public claim | No accepted measured effect | Lead | Omitted. |
| **Benefit-cost ratio** | Financial claim | No sourced deployment cost or accepted benefits | Impact | Not calculated. |

---

## 2. Known Limitations & Rules

- **Traceability**: Every number traces to an explicit artifact in `results/` or a cited source with its check date.
- **Results freeze**: 16 Oct is confirmed. Preserve the saved two-case pack and
  its original provenance; a post-freeze scenario/result change needs matched
  reruns and team review before the chart or verdict changes.
- **Observed versus simulated**: Aberdeen's roughly 35-minute gap is between
  archived detector evidence and TD's later all-lanes update, not a proven live
  early alert. Tuen Mun's −4.3% is modelled E delay, not observed road impact.
- **Visuals constraints**: Show Tuen Mun's comparison panel or sourced result
  card, not the console's Aberdeen map. Do not animate evaluated vehicles or
  highlight a recommended route without a route/trajectory asset tied to a
  reviewed run.
- **Omitted metrics**: Do not claim measured delay or travel-time saving, CO2
  reduction, benefit-cost ratio or approved operator instructions. The
  [submission manifest](submission-manifest.md) tracks export and Q&A work.
