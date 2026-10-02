# Interim Report Skeleton — Project Ripple

> **Internal submission target:** Saturday 3 October 2026
>
> **Official deadline:** Sunday 4 October 2026

Impact coordinates the report and collects a short, evidence-backed contribution from each component owner. This is an outline, not a claim that the work below is already complete. Any unmeasured result must be labelled as such.

## 1. Executive Summary & Social Problem

**Owner:** Impact  
**Status:** Draft Complete

Non-recurrent traffic disruption caused by sudden accidents along Hong Kong's critical arterial corridors creates severe network-wide friction. The Aberdeen corridor—centered on Wong Chuk Hang Road connecting the Southern District to the Aberdeen Tunnel—serves as a primary economic lifeline [docs/00-brief.md](docs/00-brief.md). Because alternative routes across the island's topography are sparse, any lane reduction during morning peak hours instantly transforms the corridor into a single point of failure [docs/05-pitch.md](docs/05-pitch.md).

<Image src="image_agent_tag_3766287884585980765" alt="Traffic congestion along major Hong Kong arterial roads leading to tunnel bottlenecks" caption="Aberdeen corridor peak-hour traffic bottlenecking" />

#### Systemic Limits of Existing Dissemination & Navigation
Current incident-response mechanisms suffer from two structural vulnerabilities:

1. **Information Lag in Official Dissemination:** Official alerts issued via Transport Department (TD) Special Traffic News exhibit measurable reporting delays. During demo candidate incident `IN-26-03365` (15 May 2026), physical queue formation was captured by detector `AID01104` at 08:55, whereas TD's initial bulletin arrived at 09:01—a 6-minute reporting gap [data/demo_shortlist.md](data/demo_shortlist.md).
2. **Uncoordinated Consumer Routing Spillover:** Commercial navigation apps (e.g., Google Maps, Waze) optimize selfishly for individual travel time. When an incident closes Wong Chuk Hang Road, uncoordinated rerouting pushes traffic onto narrow residential secondary roads (e.g., Pok Fu Lam Road, Nam Fung Road), causing secondary gridlock and blocking emergency service corridors [docs/05-pitch.md](docs/05-pitch.md).

#### The Project Ripple Interventions
Project Ripple bridges the operational gap between raw incident detection and coordinated traffic management. By linking LLM-based bilingual incident parsing with microscopic simulation and human-in-the-loop operator approval, Ripple evaluates network-wide diversion impact *before* publishing advisories [docs/03-architecture.md](docs/03-architecture.md).

#### Current Limitations of Section 1 Scope
* The economic cost model currently uses baseline statistical assumptions derived from secondary TD traffic census data; real-time monetary cost integration per incident remains `[not measured yet]`.
* Current geographical scope is strictly constrained to the Aberdeen corridor; multi-corridor cascade modeling is deferred to future project phases.

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

## 4. Operator Console & Demo Visuals

- **Owner:** Visuals
- **Starting sources:** `docs/00-brief.md` §4 (G), `src/console/`, and the current map screenshot in `docs/img/`.
- Show the current console (G) and identify which map, playback, plan-comparison, and approval features are implemented versus planned.
- Include a screenshot or video link only when the corresponding artifact exists.

## 5. Feasibility, Sustainability, Ethics & Impact

**Owner:** Impact  
**Status:** Draft Complete

#### Rollout Feasibility & Benefit-Cost Framework
Deploying Project Ripple on a single corridor requires zero additional physical infrastructure, consuming existing open feeds (TD Special Traffic News and real-time detector loops) [docs/02-data.md](docs/02-data.md). The benefit-cost evaluation weighs saved cumulative vehicle-hours against API/cloud compute overhead. For major peak-hour incidents, preventing gridlock across thousands of commuting vehicles yields significant net societal gains in time saved and reduced commercial transit delays [docs/05-pitch.md](docs/05-pitch.md).

#### Primary Fieldwork & Qualitative User Evidence
To ground HMI and prompt design in operational reality, a qualitative semi-structured interview was conducted on 26 September 2026 with an active South District Green Minibus (GMB) driver [evidence/interviews/2026-09-26-minibus-driver.md](evidence/interviews/2026-09-26-minibus-driver.md).

Key findings include:
* **Official Alert Distrust:** The driver confirmed that official radio and app alerts are too slow to be tactically useful during active shifts. Drivers rely almost exclusively on peer-to-peer WhatsApp groups and live visual tail-end queues [evidence/interviews/2026-09-26-minibus-driver.md](evidence/interviews/2026-09-26-minibus-driver.md).
* **Rejection of Macro Metrics:** Abstract promises such as "saves 740 aggregate delay hours" or "saves 12 minutes" are dismissed by operators. Drivers demand real-time speed visibility and colleague-verified flow status on candidate detour routes [evidence/interviews/2026-09-26-minibus-driver.md](evidence/interviews/2026-09-26-minibus-driver.md).
* **HMI Localization Preferences:** The driver gave positive feedback to concise Cantonese audio broadcasts anchored by specific local landmarks (e.g., *"Aberdeen Tunnel exit, queue tail at Wong Chuk Hang"*), confirming the prompt design direction [evidence/interviews/2026-09-26-minibus-driver.md](evidence/interviews/2026-09-26-minibus-driver.md).

#### Fieldwork Limitations
* **Sample Size Constraint:** This user evidence represents a single qualitative case study ($N=1$). Findings are non-representative of all commercial fleets and serve as directional qualitative design validation rather than a statistical sample [evidence/interviews/2026-09-26-minibus-driver.md](evidence/interviews/2026-09-26-minibus-driver.md).

#### Ethical Considerations & Secondary Spillover
1. **Traffic Redistribution Ethics:** Diverting traffic from main arterials onto secondary residential roads (e.g., Pok Fu Lam Road) transfers noise and tailpipe emissions to residential communities [docs/05-pitch.md](docs/05-pitch.md).
2. **Vehicle-Class Physical Constraints:** Commercial vehicles (minibuses, heavy goods vehicles) face physical slope and lane-width limitations on routes like Nam Fung Road. The LLM plan validator must explicitly incorporate vehicle-class feasibility constraints before recommending detours [docs/03-architecture.md](docs/03-architecture.md).
