# Interim Report Working Draft — Project Ripple

> **Submission update, 3 October 2026:** The Lead confirmed that the online
> interim report was submitted. The exact submitted form answers and receipt
> have not been archived here. The preparation checklist below is historical;
> this repository draft must not be treated as a verified copy of the submission.

The [23-question submission text](interim-report-submission.md) follows the
organiser's questions supplied on 3 October. This file retains the technical
evidence and contribution checklist supporting those answers.

> **Internal submission target:** Saturday 3 October 2026
>
> **Official deadline:** Sunday 4 October 2026

Impact coordinates and assembles the report. This 3 October revision integrates
the available component evidence and drafts the remaining narrative sections.
It remains a working draft awaiting Lead and Impact review, uploader confirmation
and a submission receipt. No accepted end-to-end plan benefit has been measured.

**Reminder to all owners:** add your paragraph with evidence links and remaining
limitations, and flag missing inputs to Impact promptly. Do not wait for a
successful simulation to report current progress and blockers. Impact should
confirm a collection cutoff that leaves time for Lead review before the internal
submission target on Saturday 3 October. No collection cutoff is agreed yet.

### Contribution checklist — 3 October

- [x] Lead: Reader results, architecture and D/F progress drafted in §2; final review pending.
- [x] Data: evidence-based ingestion summary in §2 and evaluator status in §3; owner review pending.
- [x] Simulation: calibration evidence and unmet targets integrated in §3.
- [x] Visuals: console progress and supported screenshot integrated in §4.
- [x] Sections 1 and 5: narrative drafted from repository evidence; Impact review pending.
- [ ] Lead + Impact: review the complete draft, confirm who uploads it, and record submission confirmation.

## 1. Executive Summary & Social Problem

- **Owner:** Impact

Ripple is a prototype incident co-pilot for traffic operators on Hong Kong's
Aberdeen corridor. It combines public detector observations and bilingual
incident messages with a planned comparison of response options. The intended
benefit is to help an operator assess whether a diversion reduces total delay
without transferring excessive disruption to neighbouring streets. This is a
hypothesis to test, not a demonstrated outcome or a replacement for existing
traffic-management operations.

The prototype now includes data ingestion, an evaluated Incident Reader,
observed-data console playback, and initial plan-generation and briefing
components. The principal remaining dependency is an accepted traffic baseline
and comparable evaluator outputs. No validated reduction in delay, emissions
or emergency travel time is available at this checkpoint. Aberdeen provides a
bounded demonstration corridor with public detector coverage; the project
excludes city-wide control and a consumer navigation application
([scope](00-brief.md), [architecture](03-architecture.md)).

The evaluation will distinguish observed traffic, an incident simulation with
no intervention, and simulations with response plans. Observations assess model
credibility; plan-versus-baseline comparisons assess potential benefit. The
4 October model decision and 14 October results freeze protect time for this
evaluation and the final demonstration ([schedule](04-plan.md)).

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
timestamp. These retrospective onset and lane choices remain hypotheses until
the scenario owners agree and document them.

### Data contribution — 2 October 2026

Ripple runs on two free, public Transport Department (TD) feeds from
DATA.GOV.HK: lane-by-lane readings (vehicle count, speed and occupancy every
30 seconds) from 28 detectors on the Aberdeen corridor, and TD's Special
Traffic News in English, Traditional Chinese and Simplified Chinese. Each feed
has a historical archive, used to replay past incidents, and a live feed, read
during an ongoing incident. The loaders (component A) collect and check both
and hand every other component one row per detector per 5-minute slot.
Unusable counts are marked rather than dropped.

TD's archives have gaps, so the data was checked before use:

- **Three news files merged.** The archive saves each language file at
  different moments, so each misses messages the others caught. Merging them by
  message ID raised incidents with a complete timeline from **68% to 85%**, and
  complete corridor accidents from 35 of 53 to 49 of 55 (22 March–21 September
  2026; `docs/02-data.md` §2).
- **Missing detector minutes.** On the demo morning (15 May, 07:55–10:35) the
  archive listed 113 files and served 80, covering 66 of 160 minutes. A missing
  minute is never counted as an empty road, and a 5-minute slot is used only
  when at least 2 of its 5 minutes and 90% of its lane readings are valid. This
  leaves **242 of 336 slots** before the crash, the same set the SUMO twin is
  scored against. Slots with fewer and more minutes differ by only 0.2 km/h
  (54.9 against 54.7 km/h), so the gaps reduce precision without biasing the
  result ([bin survival](../results/data/bin-survival_20260515-0755_1035.md)).
  The live feed publishes every minute, so live use does not have these gaps.
- **Speeds reported when no vehicle passes.** With no vehicle, the feed
  reports the speed limit as the speed (about 19% of lane readings on
  21 September) and often −1 as occupancy. The loader records these as no speed
  and 0% occupancy.
- **Silent detectors.** Three detectors (AID01105, AID01220, TDSSPWR20002)
  sent nothing on the demo morning. They are reported as missing, never
  guessed.

The demo incident was chosen from **35 screened corridor accidents**, each
compared with two ordinary days (same weekday and clock time, no corridor
incident, no public holiday). IN-26-03365 had the highest score (4.38);
IN-26-06391 is the backup
([screen result](../results/data/candidates_2026-05-15.md)). The corridor had
55 traffic accidents in 26 weeks, about two a week.

TD's 09:01 message says only that "part of the lanes" is closed, as did 25 of
the 35 screened accidents. The detectors measure each lane separately: at
AID01104, just past the crash, the slow lane carried no vehicle in five
readings in a row from 08:54:00 to 09:00:00 while the fast lane kept moving,
and both lanes were almost empty from 09:00:30, about 35 minutes before TD's
09:36 all-lanes message
([lane evidence](../results/data/lane-evidence_AID01104_20260515-0840_0920.md)).
Data therefore proposes closing the slow lane first in the replay. This choice
is still to be confirmed by the team.

Ripple handles no personal data: the detector feed has counts, speeds and
occupancy only, and the traffic news is a public announcement. The full Data
contribution, with figures, is in
[data-and-evaluation.md](data-and-evaluation.md).

### Data contribution — evidence synthesis, 3 October 2026

The loaders ingest public Transport Department detector readings and archived
Special Traffic News for the corridor. They preserve missing readings, exclude
zero-vehicle speed placeholders, and distinguish archive coverage from valid
lane readings. Merging the three archived news feeds improved complete incident
timelines from 68% to 85% in the documented March–September sample
([data methods and sample](02-data.md)). This describes archive reconstruction,
not incident-detection accuracy or proof that missing observations are random.

The selected incident is IN-26-03365 on 15 May; its screening was refreshed after
holiday and control-day checks changed
([refreshed incident screen](../results/data/candidates_2026-05-15.md)).
The full ranking and backup require refreshed screening before further use.
Count calibration retains bins with at least 40% archive coverage and 90% valid
lane readings. The saved [coverage diagnostic](../results/data/bin-survival_20260515-0755_1035.md)
supports sensitivity analysis, but similar average speeds across coverage groups
do not establish unbiased missingness. Low or zero flow alone cannot establish
a physical closure or its exact onset.

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

### Evaluator and model decision — 3 October 2026

Comparable P0/P1/P2 runs are still pending. Each comparison must share the
incident, network and demand inputs, compliance, clearance duration and seed,
and preserve provenance linking plans and metrics to those inputs. Sensitivity
across compliance and clearance assumptions follows the first accepted
comparison; common assumptions alone do not guarantee a reliable ranking.

The simplified fallback remains under review. Its saved replay injects a closure
at 08:54 while scoring a nominal pre-incident window ending at 08:55, so those
scores cannot establish no-closure calibration. The next model decision requires
a separate no-closure run, clearly separated demand-input and internal scoring
detectors, and comparable observation windows and filters. An ordinary-day
speed reference is a comparator, not a mathematical error floor. Incident queue
formation and recovery and diversion behaviour require separate validation
([review and evidence links](project-status-2026-10-03.md)).

### Data contribution — backup model and evaluation method — 2 October 2026

The project plan says that if the SUMO twin does not roughly match the
detectors by 4 October, the team switches to a simplified network. Data built
this backup so the evaluation can go ahead in either case. It is a cell
transmission model (Daganzo, 1994) of the four detector chains, divided into
24 detector-to-detector stretches. Road lengths come from the map; lanes,
speeds and joining and leaving traffic come from TD's detectors on two ordinary
Fridays (8 May and 24 April). Two values are textbook figures, stated wherever
results appear: 1,800 vehicles per hour per lane and 140 stopped vehicles per
km per lane. The code and results are in `src/fallback/` and
`results/fallback/replay_20260515.md` on the `data/week2-checks` branch, which
is not merged into `main` yet.

The backup was scored the same way as the SUMO twin: the same hour
(07:55–08:55), the same 242 five-minute counts and the same two tests.

| Scored on | Counts with GEH < 5 | Speed error | Speed error if an ordinary Friday is assumed |
|---|---|---|---|
| Backup model, all detectors | **97.1%** of 242 | 16.6% | 16.6% |
| Backup model, detectors inside the chains | **97.1%** of 205 | 17.8% | 17.8% |
| SUMO twin, 27 September test | 66.5% of 242 | 36.9% | – |
| Target (`docs/03-architecture.md` §4) | at least 85% | about 15% | – |

The counts pass the target. The speed error misses it, but it equals the error
of predicting 15 May with the ordinary Fridays' average, so the model adds no
error of its own. Two detectors that queued only on 15 May (AID01106 and
AID01216) carry most of it; without them the error inside the chains is 12.1%.
The score was recomputed from the raw readings with separately written code
and matched exactly.

For the incident replay, the flyover was closed as the detectors saw it (slow
lane from 08:54, all lanes from 09:00). This timing is provisional; a second
run closing all lanes at TD's 09:36 update is planned for 4 October.

| Detector | Queue reached it: detectors | Queue reached it: model | Cleared: detectors | Cleared: model |
|---|---|---|---|---|
| AID01104 (at the crash) | 08:55 | 08:55 | 10:00 | 10:00 |
| AID01103 | 09:05 | 09:00 | 10:15 | not by 10:35 |
| AID01102 | 09:15 | 09:10 | 10:15 | not by 10:35 |
| AID01101 | 09:50 | 09:25 | 10:05 | not by 10:35 |

The model gets the start right: the queue arrives within 5 minutes of the real
time at the three detectors nearest the crash. Later it runs too far and too
long, because the model has no diversion yet. While all lanes were closed the
detectors still counted traffic leaving the road (519 vehicles an hour by the
slip road at AID01103, and at least about 130 drivers between AID01101 and
AID01102). Without diversion, the model's queues and delays are upper bounds.

**Evaluator (E), planned for week 3 (5–11 October).** Every response plan and
a do-nothing case will be run through the chosen model on the same morning,
with one result file per run reporting total delay, its change against doing
nothing, the longest queue, corridor travel time, CO₂ and the other agreed
measures. Each plan will be repeated for 30%, 50% and 70% of drivers following
the advice and for several clearance times. Diversion will be added to the
backup model and checked against the flows above. **Plan results are not
measured yet.**

| Measure | Target | Now |
|---|---|---|
| 5-minute counts with GEH < 5, 07:55–08:55 | at least 85% | **97.1%** (backup model) |
| Average speed error per 5-minute slot | about 15%, shown with the ordinary-day floor | 16.6% (floor 16.6%) |
| When the queue reaches each detector | within 5 minutes | 3 of 4 detectors |
| Flow while all lanes are closed, model against detectors | close at every detector | not yet (no diversion) |
| Same lane as TD on the 7 accidents where TD named it | agreement rate reported | not measured yet |
| Best plan still wins at 30%, 50% and 70% compliance and across clearance times | holds across the range | not measured yet |

Details, figures and the full list of data limits are in
[data-and-evaluation.md](data-and-evaluation.md) §§6–9.

## 4. Operator Console & Demo Visuals

- **Owner:** Visuals

### Visuals contribution — 2 October 2026

Component G is a Streamlit operator console for inspecting the Aberdeen
corridor and replaying an archived incident. The current console displays 28
detector locations, colours measured speeds, and shows headline speed and
congestion indicators. It distinguishes a detector reporting no vehicles from
a missing reading, so archive gaps are visible. Play/pause, step, rewind and
timeline scrubbing let an operator inspect the recorded five-minute bins,
alongside TD's report and clearance markers. Corridor framing and a shared
light theme make the map and controls readable.

![Ripple console PDF capture from 2 October 2026, showing the recorded 15 May bin at 09:15 HKT, playback controls, speed indicators, the IN-26-03365 timeline and the pending simulation plan comparison.](img/interim-console-2026-10-02.png)

*Figure 4.1. Recorded detector-data playback for IN-26-03365 at 09:15 HKT,
captured from the local console on 2 October 2026. The plan-comparison panel
reports that completed simulation runs are still pending.
This screenshot documents the current console; it provides no evidence of
simulated rerouting or a measured plan benefit. Data: DATA.GOV.HK / Hong Kong
Transport Department. Basemap: CARTO / OpenStreetMap contributors. The capture
has a clipped right edge.*

[Original console PDF export](img/interim-console-2026-10-02.pdf).

| Feature | Status at the interim checkpoint |
|---|---|
| Detector map, speed indicators, incident timeline and playback controls | Implemented in the console. |
| Corridor framing and light theme | Implemented in the console. |
| P0/P1/coordinated-plan comparison and recommendation | Proposed workflow under review in PR #41; not integrated into the accepted console. |
| Paired simulation replay | Proposed renderer under review. Real trajectories must be bound to the evaluated simulation inputs; file hashes alone do not establish this relationship. |
| Operator approval and audit logging | Proposed implementation under review; Windows startup and audit locking require correction and testing. |
| Briefing/message panel and what-if interaction | Accepted end-to-end console integration remains pending. |
| Final demo video | Pending validated simulation outputs and completion of the operator workflow. |

The focused console and recommendation checks passed all 46 tests on 2 October.
These checks verify UI behaviour and input handling; they do not establish
traffic-model accuracy or plan effectiveness. Integration still requires
reviewed road geometry and an incident edge, completed matching plan/result
files, and paired trajectories demonstrating actual rerouting. All future
plan-benefit figures will come from simulator artifacts in `results/`.

## 5. Feasibility, Sustainability, Ethics & Impact

- **Owner:** Impact

The intended user is a traffic operator evaluating options before approving
public advice. The initial feasibility test is a bounded corridor demonstration
using open aggregate detector observations and public incident notices. A
deployment budget has not been established. A future costing should separately
record network preparation and calibration effort, compute and model inference,
hosting, maintenance, operator training and integration. Potential benefits must
first be measured as plan-versus-baseline simulator outcomes. Monetary valuation
would additionally require sourced local values of time, occupancy assumptions
and explicit operating costs; no benefit-cost ratio is claimed here.

One anonymous experienced green-minibus driver was interviewed on 26 September.
The interviewer's notes describe reliance on peer verification, concern about
alternative-route conditions, and interest in clear local and bilingual wording.
These are qualitative findings from one participant, not representative driver
preferences or measured compliance. Numerical savings presented in the concept
prompt were hypothetical stimuli, not Ripple results. Further interviews should
test these themes with operators and other road users
([interview notes and limitations](../evidence/interviews/2026-09-26-minibus-driver.md)).

The constraint validator checks residential diversion shares, school-time
restrictions, blocked roads and the emergency priority corridor. Its initial
offline implementation does not establish real route suitability: reviewed
route/context inputs and simulated distributional outcomes remain prerequisites
([D/F handoff](lead-pipeline-handoff.md)). Vehicle-class restrictions need a
separate design decision. Reduced corridor delay must not conceal additional
delay on residential streets or emergency routes.

The intended operating policy requires human review before advice is acted on,
with an audit trail for operator decisions; the console implementation remains
under review. Traffic inputs are aggregate observations and public notices,
without individual vehicle tracking. Interview evidence is anonymised. Uneven
detector coverage and archive gaps limit confidence, and missing data must remain
visible. Sustainability benefits, including lower CO₂, remain evaluation goals;
they have not been demonstrated by the current prototype.

## Submission readiness — pending Lead and Impact confirmation

### Contribution provenance checked on 3 October

| Submitted material | Repository status | Treatment in the questionnaire |
|---|---|---|
| Mark (`markwang798369`), broader report revision [#37](https://github.com/f1ymango/ripple/pull/37) | Open; author labels Sections 1 and 5 draft complete | Problem framing and interview themes retained with corrected evidence limits; unsupported causal and benefit claims excluded |
| Mark, simulation-section revision [#38](https://github.com/f1ymango/ripple/pull/38) | Merged | Saved calibration figures and unmet targets retained |
| Lead, Reader evidence [#36](https://github.com/f1ymango/ripple/pull/36) | Merged | Held-out and development results distinguished |
| Data, report contribution [#39](https://github.com/f1ymango/ripple/pull/39) | Open | Established ingestion findings used; fallback acceptance and unbiased-missingness claims excluded |
| Visuals, report and screenshot [#40](https://github.com/f1ymango/ripple/pull/40) | Merged | Observed playback described separately from pending simulated plan benefits |
| Visuals, operator workflow [#41](https://github.com/f1ymango/ripple/pull/41) | Open implementation PR | Reported as pending work, not an accepted feature |

These PRs establish submission of material to the repository. They do not
establish submission to the organiser, approval of this assembled questionnaire,
or endorsement by each contributor of the subsequent editorial changes.

### Final checks

- [ ] Review the assembled narrative and evidence links, including the screenshot's disclosed clipped right edge.
- [ ] Confirm the required submission format and any length limits against organiser instructions.
- [ ] Confirm the uploader and final approved report version.
- [ ] Upload by the official 4 October deadline and retain the timestamp and receipt.

No uploader or submission receipt is recorded in the reviewed repository
evidence. This checklist is preparation for submission, not confirmation that
submission has occurred.
