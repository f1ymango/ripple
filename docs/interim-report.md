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

### Lead contribution — 30 September 2026

Ripple uses a modular pipeline: archived bilingual Transport Department Special
Traffic News enters the Incident Reader, which extracts incident details into a
validated JSON record. Code copies identifiers, timestamps and source text;
the language model extracts road, direction, landmark, incident type and lane
wording. It preserves missing information, including `unspecified` when TD
does not identify the closed lanes. All model calls are logged, and invalid
responses are retried once before being flagged for review.

The Reader was evaluated on 100 manually labelled archived messages: 80 in
the citywide sample and 20 on the corridor. In v1, all scored fields were
correct for **50% of citywide messages and 75% of corridor messages**. After
a direction-format prompt correction and four label corrections made after
the initial results had been seen, v2 scored **75% and 85%**, respectively.
The v2 figures are development results, not a new held-out evaluation. Against
the unchanged v1 labels, v2 scored 59/80 citywide and 16/20 corridor. Remaining
errors include unsupported lane totals, road junctions and inferred landmarks.
The [score history](../data/labelled_incidents/LABELLING.md#score-history)
records the label-review chronology and limitations; the scored artifacts are
[v1](../results/reader/2026-09-25T0026_qwen3-8b_score.json),
[v2](../results/reader/2026-09-25T0048_qwen3-8b_score.json) and
[v2 against v1 labels](../results/reader/2026-09-25T0048_qwen3-8b_score_labels-v1.json).

For the selected incident, IN-26-03365, the Reader was also checked on TD's
actual 09:01 and 09:36 messages. The structured core fields matched the source:
the first message produced `["unspecified"]`, and the escalation produced
`["all"]`. One free-text `notes` sentence incorrectly described a direction
bracket; this remains a known defect. This two-message check demonstrates the
selected handoff, rather than additional accuracy evidence
([source messages](../data/demo_incident_messages.jsonl),
[Reader output](../results/reader/2026-09-29T1608_qwen3-8b.jsonl)).

The planned downstream flow is candidate plans → code-based constraint checks
→ simulation of each plan → an operator briefing grounded in saved simulator
results. P0 (no intervention), P1 (a single broadcast detour) and a coordinated
P2 are required for comparison. The Plan Generator and Briefing Writer are
implemented as an initial command-line path against the existing contracts,
with offline tests using mocked model responses. Real-model quality, evaluated
plan benefits and an accepted full incident baseline are not yet available
([handoff and limitations](lead-pipeline-handoff.md)). Human approval is
required before any advice is published or acted upon.

Three unresolved modelling details remain explicit: Simulation proposes an
08:55 physical onset based on observed queue development; TD's first report
arrived at 09:01; and Data/E still owns the initial lane choice for
`unspecified`. These are distinct from the pre-incident calibration problem.
The Reader does not resolve them by guessing a lane or changing the source
timestamp. Data's ingestion contribution and Simulation's result contribution
are still to be added by their owners.

## 3. Simulation, Evaluation & Preliminary Results

- **Owner:** Simulation; Data contributes evaluator methodology and results when available.
- **Starting sources:** `docs/03-architecture.md` §4 and `docs/00-brief.md` §6; use actual run artifacts in `results/` for all figures.
- Describe the SUMO corridor twin (C), calibration against observed detector data, and baseline-versus-plan comparison (E).
- State validation errors and scenario outcomes only from reproducible runs in `results/`; mark pending figures *not measured yet*.

### Simulation contribution — 2 October 2026

Component C runs a provisional SUMO model of the Aberdeen corridor using
OpenStreetMap and archived Transport Department detector observations. Work
completed includes left-hand conversion, direction-aware detector placement,
measurement across modelled lanes, timestamp matching, pre-incident demand
fitting and corrected route departure ordering. Runs record source hashes,
seeds and completion status and use bounded execution. The generated network
and loops remain local and under review; the current artifacts do not yet
constitute a portable, reviewed network release.

Calibration uses the selected incident's **15 May 2026, 07:55–08:55 HKT**
observations after a 15-minute warm-up. No incident closure is applied in this
window. Counts are scored only where archive coverage is at least 40% and
at least 90% of lane readings are valid. The 2 October controlled comparison
kept network, demand, routes and seed fixed, changing only an unsupported
16.7 m/s vehicle speed ceiling so vehicles could follow network limits.

| Pre-incident metric | Reference | Speed-ceiling removal | Target |
|---|---:|---:|---:|
| Count bins with GEH < 5 (242 bins) | 66.53% | 66.94% | At least 85% |
| Speed MAPE (296 common bins) | 36.94% | 41.36% | Approximately 15% or lower |
| Teleports | 68 | 53 | Review required |
| Vehicles waiting to enter at run end | 2,405 | 2,390 | Review required |

Both runs completed all 4,500 simulation seconds without route-loading errors.
Although teleports decreased, speed error worsened and both calibration
targets remain unmet. These are calibration results against the fitted hour,
not independent validation. The earlier 30 September result of 66.94% GEH
also covered the pre-incident hour; it used different flow scheduling and is
not the reference for this paired comparison. Evidence:
[reference run](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/oct02-reference.json),
[modified run](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/oct02-network-speed.json),
[common-bin comparison](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/oct02-comparison.json).
Links are pinned to the simulation commit because those artifacts are awaiting merge.

The source audit found inconsistent lane-access tags at a tunnel transition
and a model lane permitting passenger cars with no onward connection. Further
review is needed to distinguish source/conversion errors from legitimate lane
drops. Three detector lane-count conflicts and three missing May-window lane
scopes also remain unresolved. Teleports and insertion queues can distort
physical queue development, travel times and plan rankings; they cannot be
treated as cosmetic warnings. See the
[diagnosis and source audit](https://github.com/f1ymango/ripple/blob/be7bd65/docs/calibration-progress-2026-10-02.md).

**Full incident P0-versus-observed validation and P0/P1/P2 benefit comparisons
are not measured yet in an accepted run.** P0 represents the incident with no
response intervention. Simulation proposes an 08:55 physical onset, 09:36
all-lanes phase and 10:02 reopening, pending agreement with Data/E. TD's first
message was at 09:01; operator actions must respect information availability.
Data/E's initial `unspecified` lane default remains a disclosed modelling
decision to agree. It cannot explain the earlier no-closure calibration failure.

A separate full-horizon
[traffic-only diagnostic video](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/aberdeen-full-traffic-sept30.mp4)
demonstrates execution with no assumed closure, not validated incident
reproduction. Next work prioritises tunnel connections, route contributions
and detector placement at the worst count locations. Data's simplified-network
fallback should remain active for the 4 October decision; its methodology and
evaluation status are for Data to report.

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
