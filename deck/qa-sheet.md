# Presentation Q&A — 16 October frozen two-case cut

This is current Lead source copy for Impact's final presenter review. It
supersedes the earlier Aberdeen-only Q&A in this file. Reconcile any open
[Impact Q&A PR #69](https://github.com/f1ymango/ripple/pull/69) before export;
do not combine answers from different result sets. The
[two-case evidence pack](../docs/demo-two-incidents-2026-10-16.md) and
[Simulation's final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md)
are the claim anchors.

## Case results and evidence boundaries

### Q1. What did Ripple achieve in the two cases?

In the Aberdeen replay, tested P0 and P2 tied under the team's ranking rule,
so the console withheld a plan recommendation. In the Tuen Mun prototype
simulation, the frozen capacity-bounded P2 advised 11% of the eligible group
via Castle Peak Road. Across 18 scored conditions, P2 ranked before P0 and
blanket-advice P1: mean **−4.3% modelled E delay** versus P0, with a paired
95% interval from **−5.6% to −3.0%**. P1 was about **+37%** versus P0 on the
same aggregate measure. These are simulated comparisons, not measured road
savings. See the [saved plans, rankings and provenance](../results/demo-oct16/).

### Q2. Can we say the Tuen Mun plan saved traffic delay on the actual road?

No. The P0 runs pass the team's formal validation-v2 targets for the scored
grid, but Simulation found that the replayed queue moved about 41–43 km/h
where TD's lane observations were about 20.6 km/h; it also cleared early and
discharged too much traffic after reopening. This permits a **labelled
modelled-candidate** result, not a measured traffic-benefit or physically
validated incident-replay claim. CO₂, travel-time and benefit-cost savings
remain unmeasured. Show the short queue-limit caption next to the Tuen Mun
chart, not only in the appendix.

### Q3. Did P2 win in every scenario, and which decision rule was used?

P2 had lower delay in **17 of the 18** scored Tuen Mun cells. The earlier
team-wide rule, used by the evaluator, briefing selection and console, ranks
plans by the paired 95% interval over the counted cells; under that rule P2
ranks first. A stricter Tuen Mun protocol required a win in **every** cell;
one cell failed it. Both readings are disclosed. The interval describes the
saved simulation grid, not uncertainty about real-world road savings or 18
independent incident days.

### Q4. Did the AI choose the 11% share or calculate the −4.3% result?

No. The recorded plan generator proposed an 80% advice share. A deterministic
Lead capacity rule reduced it to **11% before the fresh-seed comparison**.
The evaluator, not the language model, computed the delay and ranking. The
11% is a capacity-bounded candidate, not a proven optimal share. The AI may
propose numerical **actions**; it does not author simulator-derived benefit
metrics. See the [plan handoff](../docs/tuen-mun-lead-plans-2026-10-15.md).

### Q5. Is Aberdeen evidence that no intervention could ever help?

No. It shows that the **tested** P0 and P2 were tied in this replay and the
system withheld advice. Archived detector readings went empty well before
TD's later all-lanes update, but this is a retrospective record gap, not a
demonstrated live early warning or proof of the exact physical closure time.
See the [Aberdeen source review](../docs/incident-p0-verdict-2026-10-14.md).

## GenAI, operator control and delivery

### Q6. How well did the Incident Reader perform?

Its initial held-out all-fields-correct evaluation scored **50% citywide**
(40/80) and **75% corridor** (15/20). After prompt and label corrections
informed by that evaluation, development scores were **75% citywide** (60/80)
and **85% corridor** (17/20); these are not a fresh held-out test. The 1
October prompt experiment was not adopted. See the
[labelling and score history](../data/labelled_incidents/LABELLING.md).

### Q7. Does Ripple issue live instructions or control signs and signals?

No. The demo uses archived messages, recorded model inference and saved
simulation runs. The operator console can display a recommendation or
withhold one, and its approval workflow is logged; it does not actuate road
equipment. The Tuen Mun bilingual briefing is a provenance-bound
**single-cell draft**, not an approved public instruction. Lead's 16 October
content review found a literal drafting instruction in its Chinese text, so
that text stays out of public copy until human-corrected and operator-reviewed
([delivery checklist](../docs/2026-10-16-freeze-and-delivery-checklist.md)).

### Q8. What remains between the frozen prototype and submission?

Impact must finish a rendered deck with the organiser's mandatory cover and
embedded prototype proof; Visuals must deliver a reviewable two-case video
and source manifest; Lead and Impact must verify captions, links, uploader
access and the receipt. The internal target is **17 October**. The
[official 2026 instructions](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/)
set **18 October, 23:59 HKT** as the hard deck deadline and say the uploaded
slides cannot be changed afterward.

## Source check for presenters

| Claim | Primary source | Use |
| --- | --- | --- |
| Aberdeen tie and withheld recommendation | [Two-case pack](../results/demo-oct16/aberdeen/) | Tested replay only; no global no-benefit claim |
| Tuen Mun P2 −4.3%, P1 about +37%, 18 scored cells | [Ranking and provenance pack](../results/demo-oct16/tuen-mun/) | Modelled E-delay comparison only |
| Tuen Mun queue and recovery limitation | [Simulation final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md) | Keep a visible caption next to the chart |
| Reader held-out and development accuracy | [Score history](../data/labelled_incidents/LABELLING.md) | Do not present development scores as new held-out results |
| Interview evidence | [One anonymous minibus-driver note](../evidence/interviews/2026-09-26-minibus-driver.md) | Qualitative design input, not representative or expert validation |

The [submission manifest](submission-manifest.md) tracks source artifacts
separately from the deck, video and access items still awaiting delivery.
