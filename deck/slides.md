# Presentation Deck Draft (12 Oct evidence review)

---

## Slide 1: Problem & Real-World Impact — convincing framing

- **Operational gap**: public incident advice can send everyone toward the
  same alternative, while individually optimised routes can shift congestion
  rather than reduce system-wide delay ([project brief](../docs/00-brief.md)).
- **Real case**: archived TD messages and detector readings show the 15 May
  IN-26-03365 incident. The 09:01 and 09:36 times are observed publication
  times; the initial slow-lane phase and 08:55 physical onset are model
  assumptions, not confirmed closure facts
  (`../results/data/closed-lanes_AID01104_20260515-0840_1010.md`).
- **User signal, not validation**: one experienced green-minibus driver valued
  local route status and verification more than aggregate saving claims. This
  is one qualitative interview, not a representative survey or expert sign-off
  ([notes](../evidence/interviews/2026-09-26-minibus-driver.md)).

---

## Slide 2: Technical Innovation — appropriate GenAI

- **Why GenAI**: Qwen3:8b turns variable bilingual incident prose into a fixed,
  validated JSON contract. The video uses an existing logged input/output pair,
  visibly labelled as recorded inference rather than a live call
  ([saved output](../results/reader/2026-09-29T1608_qwen3-8b.jsonl)).
- **Measured Reader performance**: the initial held-out all-fields-correct
  evaluation scored **50% citywide** and **75% corridor**. After prompt and
  label corrections informed by that evaluation, the development scores were
  **75%** (60/80) and **85%** (17/20); they are not fresh held-out results.
  The separate 1 October experiment scored 62.5% and 60% and was not adopted
  ([score history](../data/labelled_incidents/LABELLING.md)).
- **Guardrail**: the LLM may parse messages, propose plans and draft briefings;
  it never supplies a metric the simulator can compute. Prompts and calls are
  logged, strict schemas are validated, and the evaluator owns numerical
  outcomes ([architecture](../docs/03-architecture.md)).

---

## Slide 3: Prototype / Demo — what works and what is simulated

- **Works with real archived inputs**: timeline playback shows bilingual TD
  messages, five-minute detector observations, coverage labels and a road
  graph for IN-26-03365. The incident callout is approximate and route colours
  are geometry context, not advice
  ([playback guide](../docs/console-observed-playback.md)).
- **Working capability demonstration**: plan/briefing provenance checks,
  operator decisions and audit logging are implemented and tested with clearly
  named fixtures. Fixture screens must remain visibly labelled
  ([workflow guide](../src/console/OPERATOR_WORKFLOW.md)).
- **Diagnostic only**: Data's evaluator PR includes an incident P0 and rehearsal
  P1/P2, but the rehearsal plans are stand-ins and Data/Simulation retain
  NO-GO for public plan ranking ([PR #55 review](../docs/2026-10-11-evaluator-integration-review.md)).
- **Reproducibility**: saved results and provenance sidecars bind plans,
  generation inputs and simulation inputs. Hash agreement prevents mixing
  files; it does not establish behavioural validity.

---

## Slide 4: Feasibility & Impact — measured boundaries

- Local Qwen3:8b, SUMO and open aggregate TD data are workable prototype
  choices. A deployment estimate still needs a priced configuration, measured
  usage and support assumptions; no monthly operating cost is claimed
  ([costing](costing.md)).
- Archive gaps make detector counts uncertain: calibration uses count bins only
  at at least 40% archive coverage and 90% valid lane readings. Missing data is
  labelled, never converted to zero traffic ([data rules](../docs/02-data.md)).
- **Delay saving, travel-time benefit and CO2 reduction**: no accepted
  incident-specific claim. **BCR**: not calculated. The 14 October freeze locks
  supported evidence; it does not imply outstanding validation will succeed.

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
- **14 Oct**: freeze accepted results and the claims they support. Unsupported
  plan benefits remain omitted.
- **17 Oct**: internal submission target for deck, prototype and video;
  official deadline 18 October.
- Current artifact status and owners are tracked in the
  [submission manifest](submission-manifest.md).
