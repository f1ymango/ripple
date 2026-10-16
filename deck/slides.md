# Presentation Deck Draft (16 Oct Two-Incident & GenAI Update)

> **Export blocker — mandatory cover slide:** this Markdown draft starts with
> the problem slide, not the organiser's required first page. Before export,
> Impact must add a cover with the verified team name, project title, thematic
> track, a description of at most 30 words, and each member's full name and
> university. Use the assigned `Team Number – [Team Name]` filename, and place
> the accessible prototype/video link inside the one-file deck. See the
> [2026 submission rules](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/)
> and [delivery checklist](../docs/2026-10-16-freeze-and-delivery-checklist.md).
> Suggested 27-word description: “Ripple is an AI incident co-pilot that reads
> traffic reports, tests response plans in a road-network simulation, and helps
> operators decide when to advise—or hold back.” Verify the final word count
> after Impact edits it.

---

## Slide 1: Problem & Real-World Impact — convincing framing

- **Operational gap**: public incident advice can send everyone toward the
  same alternative, while individually optimised routes can shift congestion
  rather than reduce system-wide delay ([project brief](../docs/00-brief.md)).
- **Real case (Aberdeen IN-26-03365)**: archived TD messages and detector readings
  show the 15 May incident. In retrospect, detectors show the flyover empty from
  09:00:30; TD's all-lanes-closed update came at 09:36. That is a roughly
  **35-minute gap in the archived record**, not a demonstrated live alert
  (`../results/data/closed-lanes_AID01104_20260515-0840_1010.md`).
- **User signal, not validation**: one experienced green-minibus driver valued
  local route status and verification more than aggregate saving claims. This
  is one qualitative interview, not a representative survey or expert sign-off
  ([notes](../evidence/interviews/2026-09-26-minibus-driver.md)).

---

## Slide 2: Technical Innovation — appropriate GenAI & Self-Checking Guardrails

- **Why GenAI**: Qwen3:8b turns variable bilingual incident prose into a fixed,
  validated JSON contract. The planned video pickup uses a saved input/output pair,
  visibly labelled as recorded inference rather than a live call
  ([saved output](../results/reader/2026-09-29T1608_qwen3-8b.jsonl)).
- **Measured Reader performance**: the initial held-out all-fields-correct
  evaluation scored **50% citywide** and **75% corridor**. After prompt and
  label corrections informed by that evaluation, the development scores were
  **75%** (60/80) and **85%** (17/20); they are not fresh held-out results
  ([score history](../data/labelled_incidents/LABELLING.md)).
- **Guardrail & Self-Checking (Honest Co-pilot)**: the LLM may parse messages, propose
  plans and draft briefings; it never supplies a metric the simulator can compute.
  The evaluator compares candidates over matched simulation conditions and can
  withhold a recommendation when no plan ranks first. A separate human-led
  source review identified Aberdeen P2's unsourced signal timing; that was not
  automatically caught by the evaluator ([architecture](../docs/03-architecture.md),
  [source review](../docs/incident-p0-verdict-2026-10-14.md)).
- **Plan generation exercised**: local Qwen3:8b produced saved P0/P1/P2 drafts after
  validation retries. In Aberdeen, P0 and P2 tie under the team's ranking rule,
  so Ripple's console withholds a recommendation
  ([actual outputs and review](../docs/demo-two-incidents-2026-10-16.md)).

---

## Slide 3: Two-Incident Prototype — Aberdeen Refusal vs. Tuen Mun Active Advice

- **Works with real archived inputs**: timeline playback shows bilingual TD
  messages, five-minute detector observations, coverage labels and a road
  graph ([playback guide](../docs/console-observed-playback.md)).
- **Aberdeen Case (Observed Incident; Simulated Refusal)**: TD later reported
  both flyover lanes closed; the archived detector timeline shows traffic
  disappearing earlier. In the model, drivers use Wong Chuk Hang Road, the only open bypass.
  P0 and P2 tie under the team's ranking rule, so the console withholds a
  recommendation.
- **Tuen Mun Road Case (Simulated Positive Prototype)**: Demonstrates active routing value.
  In the matched grid, blanket broadcast (P1) has **+37% modelled delay**;
  capacity-bounded 11% advice (P2) ranks ahead of P0/P1 under the team's
  aggregate rule over 18 scored cells (**-4.3% modelled delay**; 95% interval
  -5.6 to -3.0). It does not win every individual cell.
  *Chart caption: Modelled comparison, not a measured road saving. The observed
  queue was slower and lasted longer than the replay*
  ([Simulation's final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md)).
- **Reproducibility**: saved results and provenance sidecars bind plans,
  generation inputs and simulation inputs (`results/demo-oct16/`).

---

## Slide 4: Feasibility & Impact — measured boundaries

- Local Qwen3:8b, SUMO and open aggregate TD data are workable prototype
  choices. A deployment estimate still needs a priced configuration, measured
  usage and support assumptions; no monthly operating cost is claimed
  ([costing](costing.md)).
- Archive gaps make detector counts uncertain: calibration uses count bins only
  at at least 40% archive coverage and 90% valid lane readings. Missing data is
  labelled, never converted to zero traffic ([data rules](../docs/02-data.md)).
- **Delay saving, travel-time benefit and CO2 reduction**: Aberdeen delay savings
  remain strictly **BLANK**. Tuen Mun delay reduction is reported as a modeled simulation
  candidate (-4.3%). **BCR**: not calculated. The confirmed 16 October freeze locks
  supported evidence.

---

## Slide 5: Sustainability, Ethics & Human Control

- **Human authority**: Ripple recommends; it never controls. No message, sign
  or signal action occurs without an identified operator decision, and the
  audit trail records views, approvals, rejections and edits.
- **Privacy**: the prototype uses aggregate open traffic data—no vehicle
  identifiers or individual tracking.
- **Coverage bias**: detector coverage favours strategic roads. A responsible
  deployment reports corridor confidence and withholds recommendations when
  observations or route evidence are inadequate.
- **Route protection**: the plan validator rejects excessive residential-road
  diversion, school-street use at peak times, blocked routes, conflicting
  shares and diversion onto the emergency-priority corridor. These constraints
  are implemented, while real route/context acceptance remains outstanding.

---

## Slide 6: Delivery Roadmap

- **12 Oct**: review the observed-data demo, recorded-Reader pickup, deck,
  evidence manifest and Q&A wording.
- **15 Oct checkpoint**: the two-incident evidence pack and Markdown slide draft
  arrived; an editable/rendered deck and playable two-case video are still due.
- **16 Oct (confirmed)**: freeze accepted results and claims; review the final
  package delta. Cutoff hour is unconfirmed. Unsupported benefits remain omitted.
- **17 Oct**: internal submission target for deck, prototype and video;
  official deadline 18 October.
- Current artifact status and owners are tracked in the
  [submission manifest](submission-manifest.md).
