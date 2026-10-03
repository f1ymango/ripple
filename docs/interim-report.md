# Interim Report Working Draft — Project Ripple

> **Internal submission target:** Saturday 3 October 2026
>
> **Official deadline:** Sunday 4 October 2026

Impact coordinates and assembles the report, collecting a short, evidence-backed
contribution from each component owner. The Lead contribution below is drafted;
the other sections remain outlines pending contributions. Any unmeasured result
must be labelled as such.

**Reminder to all owners:** add your paragraph with evidence links and remaining
limitations, and flag missing inputs to Impact promptly. Do not wait for a
successful simulation to report current progress and blockers. Impact should
confirm a collection cutoff that leaves time for Lead review before the internal
submission target on Saturday 3 October. No collection cutoff is agreed yet.

### Contribution checklist — 30 September

- [x] Lead: Reader results, architecture and D/F progress drafted in §2; final review pending.
- [ ] Data: ingestion and data limitations in §2; evaluator methodology/status in §3.
- [ ] Simulation: calibration and validation evidence, limitations and next steps in §3.
- [ ] Visuals: console progress and a supported screenshot in §4.
- [ ] Impact: problem framing and summary in §1; feasibility, ethics and interview evidence in §5; assemble all sections.
- [ ] Lead + Impact: review the complete draft, confirm who uploads it, and record submission confirmation.

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

## 3. Simulation Evaluation & Preliminary Results

**Owner:** Simulation (Data contributes evaluator methodology and results)  
**Status:** Contribution Integrated (2 October 2026)

Component C runs a provisional SUMO model of the Aberdeen corridor using OpenStreetMap and archived Transport Department detector observations. Work completed includes left-hand conversion, direction-aware detector placement, measurement across modelled lanes, timestamp matching, pre-incident demand fitting, and corrected route departure ordering.

---

### 📊 Pre-Incident Calibration Performance

Calibration uses the selected incident's **15 May 2026, 07:55–08:55 HKT** observations after a 15-minute warm-up. Counts are scored only where archive coverage is at least 40% and at least 90% of lane readings are valid. 

The 2 October controlled comparison kept network, demand, routes, and seed fixed, changing only an unsupported 16.7 m/s vehicle speed ceiling so vehicles could follow network limits:

| Pre-incident Metric | Reference | Speed-Ceiling Removal | Target / Benchmark | Status |
| :--- | ---: | ---: | ---: | :---: |
| **Count bins with GEH < 5** (242 bins) | 66.53% | **66.94%** | At least 85.00% | ⚠️ Unmet |
| **Speed MAPE** (296 common bins) | 36.94% | **41.36%** | $\le 15.00\%$ | ⚠️ Unmet |
| **Teleports** | 68 | **53** | Review required | 🔄 Improved |
| **Vehicles waiting to enter at run end** | 2,405 | **2,390** | Review required | 🔄 Improved |

> **Key Finding:** Both runs completed all 4,500 simulation seconds without route-loading errors. Although teleports decreased (68 → 53), speed error (MAPE) worsened, meaning both calibration targets remain unmet for independent validation.

#### Reproducible Artifacts & Evidence
* 📄 **Reference Run JSON:** [`results/twin/oct02-reference.json`](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/oct02-reference.json)
* 📄 **Modified Run JSON:** [`results/twin/oct02-network-speed.json`](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/oct02-network-speed.json)
* 📊 **Paired Comparison:** [`results/twin/oct02-comparison.json`](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/oct02-comparison.json)

---

### 🔍 Source Audit & Diagnostic Findings

1. **Lane-Access Discrepancies:** Inconsistent lane-access tags were identified at a critical tunnel transition, allowing passenger cars onto a lane with no onward connection.
2. **Unresolved Scopes:** Three detector lane-count conflicts and three missing May-window lane scopes remain unresolved.
3. **Physical Queue Distortion:** Teleports and insertion queue delays directly distort travel times and plan rankings; they are treated as operational bottlenecks rather than cosmetic warnings. See full [Diagnosis and Source Audit](https://github.com/f1ymango/ripple/blob/be7bd65/docs/calibration-progress-2026-10-02.md).

---

### ⚠️ Pending Evaluation & Limitations

* **Full incident P0-versus-observed validation and P0/P1/P2 benefit comparisons are `[not measured yet]` in an accepted run.**
* **Timeline Assumptions:** Simulation proposes an 08:55 physical onset, 09:36 all-lanes phase, and 10:02 reopening (pending alignment with Data/E). TD's first public alert arrived at 09:01.
* **Fallback Strategy:** Data's simplified-network fallback remains active for the 4 October submission decision.
* 🎥 **Diagnostic Video:** [Full-horizon traffic-only diagnostic video](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/aberdeen-full-traffic-sept30.mp4) (Demonstrates flow execution with no assumed closure).

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
