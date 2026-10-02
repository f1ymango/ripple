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

## 3. Simulation, Evaluation & Preliminary Results

- **Owner:** Simulation; Data contributes evaluator methodology and results when available.
- **Starting sources:** `docs/03-architecture.md` §4 and `docs/00-brief.md` §6; use actual run artifacts in `results/` for all figures.
- Describe the SUMO corridor twin (C), calibration against observed detector data, and baseline-versus-plan comparison (E).
- State validation errors and scenario outcomes only from reproducible runs in `results/`; mark pending figures *not measured yet*.

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
- **Starting sources:** `docs/00-brief.md` §4 (G), `src/console/`, and the current map screenshot in `docs/img/`.
- Show the current console (G) and identify which map, playback, plan-comparison, and approval features are implemented versus planned.
- Include a screenshot or video link only when the corresponding artifact exists.

## 5. Feasibility, Sustainability, Ethics & Impact

- **Owner:** Impact
- **Starting sources:** `docs/05-pitch.md` §§5–6 and `evidence/interviews/2026-09-26-minibus-driver.md` (one qualitative interview).
- Present the single-corridor rollout costing and benefit-cost framework, with assumptions and sources.
- Summarise interview evidence as qualitative, including the number and profile of participants; avoid treating one interview as representative.
- Discuss spillover, privacy, and the limits of the current evidence.
