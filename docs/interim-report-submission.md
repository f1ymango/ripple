# Ripple — Interim Progress Report

**Prepared:** 3 October 2026 · **Track:** Green Transport & Smart Mobility

Finalization candidate aligned to the 23 questions supplied from the organiser's
website. Team approval, form length limits and submission receipt remain pending.
The [technical evidence report](interim-report.md) preserves the detailed results.

## Problem and Scope

### 1. What specific problem or pain point is your project addressing?

During a road incident, traffic operators must interpret changing reports and
assess alternatives without simply transferring congestion to another road.
Ripple addresses the difficulty of comparing corridor-wide consequences before
issuing advice. Our demonstration covers the Aberdeen corridor, including Wong
Chuk Hang Road and the Aberdeen Tunnel. We are testing whether an operator tool
can turn public incident messages and detector observations into an auditable
comparison of response options.

### 2. What research have you conducted to understand the problem better?

We examined archived Transport Department (TD) detector readings and bilingual
Special Traffic News, screened corridor incidents against ordinary-day traffic,
and selected IN-26-03365 on 15 May. Combining three archived news feeds increased
complete incident timelines from 68% to 85% in our documented March–September
sample. These are archive-reconstruction findings, not incident-detection accuracy
([data methods](02-data.md), [refreshed incident screen](../results/data/candidates_2026-05-15.md)).

We also conducted one qualitative interview with an experienced Aberdeen/Pok Fu
Lam green-minibus driver and reviewed existing traffic-management arrangements.
The participant valued verification of alternative-route conditions and clear
local wording. One interview cannot establish general driver preferences
([interview notes](../evidence/interviews/2026-09-26-minibus-driver.md)).

### 3. Why is this problem significant? Who does it affect?

Incident disruption affects commuters, public-transport passengers, commercial
drivers and operators. Diversions may also affect residents along alternative
routes and access for emergency services. Reducing total delay while accounting
for these unequal effects is our intended contribution. We have not yet measured
Ripple's effect on travel time, emissions, emergency access or economic costs.

### 4. What existing solutions are available and how do they fall short?

Hong Kong already has coordinated incident management. TD's Traffic and Incident
Management System supports incident detection, contingency plans, information
dissemination and coordination of traffic-control systems
([TD's description](https://www.td.gov.hk/en/transport_in_hong_kong/its/its_achievements/traffic_and_incident_management_system/index.html)).
Public notices, navigation tools and driver communication networks also help
people respond. Our interview participant nevertheless wanted to verify that an
alternative route was moving before trusting advice.

Our proposed gap is a bounded, inspectable comparison of response options using
open data, with bilingual explanations for an operator. We have not established
that existing operational systems lack equivalent functions, or that commercial
navigation caused the congestion observed in our selected incident.

## Proposed Solution

### 5. Describe the primary objectives of your project.

Our objectives are to extract structured incident information from bilingual
messages, validate a corridor traffic model, compare no intervention (P0), a
single broadcast detour (P1) and coordinated plans (P2 onward), and explain the
results to an operator. The language model reads messages, proposes plans and
drafts explanations; simulation code computes all traffic outcomes. The intended
workflow requires human approval before advice is acted on
([architecture](03-architecture.md)).

### 6. What are the boundaries of your project?

We focus on one corridor and an archived incident demonstration. We will not
provide city-wide traffic control, train a custom model, build a consumer
navigation app, or actuate real signals and signs. Diversions, signal changes
and driver compliance are simulation assumptions. Real operational deployment
and integration are beyond the hackathon prototype ([scope](00-brief.md)).

### 7. What assumptions are you making about the problem and its context?

We assume public observations can support a sufficiently credible corridor
model; current calibration has not yet met our targets. Demand, route suitability,
driver compliance and clearance duration require explicit assumptions and
sensitivity checks. Missing archive snapshots are not assumed to be random.
TD's reported times are distinct from physical onset: low flow alone does not
prove a closure or its exact timing. Initial lane choice for an unspecified
closure and retrospective onset hypotheses require scenario-owner agreement.

### 8. Who is your target audience or user base?

The primary user is a traffic operator reviewing response options. Drivers and
passengers are intended beneficiaries rather than users of a new consumer app.
The interface aims to support bilingual text, familiar landmarks, visible
uncertainty and reviewable options. Operator usability and accessibility still
need testing, including legibility, non-colour cues and the hardware needed to
run the console.

### 9. Who is your client, the group paying for the solution?

Prospective clients are TD and tunnel or highway operators. These are proposed
customer groups, not confirmed partners or paying customers. We have no agreed
procurement path, deployment budget or benefit-cost ratio. Costing must include
calibration, integration, compute, maintenance and training as well as hosting.

### 10. How did you gather information about audience needs, including testing?

On 26 September we conducted a structured interview and concept-response exercise
with one anonymous experienced green-minibus driver. The notes indicate interest
in current alternative-route conditions, peer verification and local bilingual
wording. This was concept feedback, not a usability trial of a completed console.
The numerical savings in the interview stimulus were hypothetical and are not
performance evidence. We plan further interviews and an operator workflow test;
neither representative user validation nor measured compliance is available yet.

## Teamwork

### 11. How is your team structured, and what roles does each member play?

Our five-person team has distinct responsibilities:

| Role | Responsibility |
|---|---|
| Lead | Scope, architecture, Incident Reader, Plan Generator, Briefing Writer and integration |
| Data | Archive ingestion, scenario evaluation and experiments |
| Simulation | Corridor model, demand calibration and validation |
| Visuals | Operator console and demonstration video |
| Impact | Problem research, interviews, interim report and pitch evidence |

The team spans CSE, Physics and CSE/Quantitative Finance. Each area has one
decision owner; scope changes go to the Lead ([team plan](04-plan.md)).

### 12. What communication strategies support effective collaboration?

Our agreed cadence is one 20-minute Wednesday-afternoon sync, covering completed
work, current work and blockers. Urgent issues use asynchronous team chat with
a stated deadline for objections. Shared JSON contracts define module boundaries,
and GitHub pull requests make integration reviewable. Each owner contributes
evidence and limitations to the report; Impact assembles it and Lead reviews it.

## Progress

### 13. What have you achieved so far?

- **Data:** loaders and screening tools handle incident status changes, archive
  gaps and zero-vehicle speed placeholders for the corridor's 28 detectors.
- **Incident Reader:** 100 messages were labelled. Initial held-out all-field
  accuracy was 50% on 80 citywide messages and 75% on 20 corridor messages.
  Subsequent prompt/label corrections produced development scores of 75% and
  85%; these are not new held-out results
  ([score history](../data/labelled_incidents/LABELLING.md#score-history)).
- **Simulation:** SUMO runs and has detector-placement, connectivity and demand
  diagnostics. In the saved 2 October controlled comparison, removing a global
  speed ceiling changed count bins meeting GEH < 5 from 66.53% to 66.94% and
  speed MAPE from 36.94% to 41.36%. Both targets remain unmet
  ([saved comparison](https://github.com/f1ymango/ripple/blob/be7bd65/results/twin/oct02-comparison.json)).
- **Plans and briefings:** initial components have schema, constraint and
  provenance checks with offline tests; real comparable evaluator outputs are
  still required ([handoff](lead-pipeline-handoff.md)).
- **Console:** detector maps, speed indicators and archived timeline playback
  are implemented ([captured console](img/interim-console-2026-10-02.png)).

No accepted end-to-end plan comparison or measured traffic benefit is available.

### 14. What part of your project are you currently working on?

The active work is baseline validation and the SUMO/fallback decision, evaluator
comparability and provenance, and console workflow integration. The fallback
and proposed recommendation/approval workflow remain under review. We are also
assembling the interim evidence into this questionnaire rather than presenting
unfinished integrations as completed features.

### 15. What are your immediate next steps or milestones?

By 4 October, complete report review/submission and make the model decision using
comparable no-closure diagnostics. Next, agree incident lane/timing assumptions,
validate queue recovery, and produce P0/P1/P2 comparisons using reviewed route
inputs. During 5–11 October, prioritise sensitivity analysis and the tested
operator workflow. Freeze results on 14 October, then finish the video and deck
for the 18 October final deadline. Model failure will narrow the demonstration
and claims rather than justify unsupported benefit figures ([schedule](04-plan.md)).

### 16. How will you evaluate success as the project progresses?

We separate software correctness, model validity and potential benefit. Reader
accuracy is checked against labelled messages. Model targets are GEH < 5 for at
least 85% of eligible count bins and approximately 15% or lower speed MAPE.
Calibration must use no-closure runs and explicit observation filters; incident
queue formation and recovery need separate validation.

Plan comparisons will share demand, network, incident, compliance, clearance and
seed, with saved input provenance. Metrics include delay, queue length, travel
time, emergency travel time, CO₂ and residential delay share. Compliance and
clearance sweeps will test sensitivity. Console tests and operator feedback will
assess whether sources, uncertainty and decisions are understandable. Passing
software tests alone does not validate traffic outcomes.

## Challenges

### 17. What challenges have you encountered, and how did you address them?

Archive gaps and incident status changes initially obscured complete timelines;
we combined feeds and corrected status handling. Zero-vehicle speed placeholders
and offline lanes required explicit missing-data treatment. Ambiguous bilingual
messages caused Reader errors; we reviewed labels and prompts while distinguishing
development results from held-out evaluation. Simulation diagnostics identified
lane-access, demand-entry and speed-limit issues, but calibration remains below
target. The proposed console workflow also has a Windows locking/startup issue
that must be corrected before integration ([review record](project-status-2026-10-03.md)).

### 18. What upcoming challenges do you foresee, and how will you address them?

The main risk is spending the remaining schedule on calibration without a
credible plan comparison. We will time-box the model decision and assess a
simplified fallback honestly. Its current replay overlaps the nominal calibration
window with an injected closure, so a separate no-closure run is required.
Uncertain incident timing, route suitability and compliance can change rankings;
we will disclose assumptions and test sensitivity. Real operator access and
additional interviews may be limited, so we will report the actual sample and
avoid claiming broad user validation.

## Resources

### 19. What resources have you used, and how have they contributed?

TD/DATA.GOV.HK public detector and incident archives provide observations and
source messages. OpenStreetMap supports network construction. SUMO with TraCI
and sumolib supports simulation and diagnostic outputs. Python, pandas and
JSON Schema support data processing and validation. Ollama/Qwen3:8b supports
local Reader experiments; saved prompts and responses preserve evidence.
Streamlit, pydeck and Altair support the console. GitHub, pytest and CI support
review and software checks ([dependencies](../requirements.txt),
[data documentation](02-data.md), [AI logs](../evidence/ai-log/)).

### 20. What resources do you need but currently lack?

The key missing inputs are an accepted portable model baseline, reviewed real
route/context data, agreed incident assumptions, comparable evaluator results
and trajectories tied to those runs. We also need operator feedback, additional
interviews, and deployment cost and integration expertise. The reviewed evidence
does not establish a specific hardware purchase requirement. These gaps prevent
us from promising a deployment budget or operational readiness.

## Learnings

### 21. What have you learned so far?

Data availability is not the same as representative evidence: archive gaps,
sensor outages and placeholder values need different treatment. A plausible
traffic animation does not establish a valid baseline. Prompt improvements
measured on previously inspected labels are development evidence. The interview
also suggests that trust in local route conditions deserves further testing.
Shared contracts and evidence-linked reviews help expose dependencies early.

### 22. How has your understanding evolved?

We began with an incident-to-coordinated-response concept. Work on real data
showed that calibration, uncertainty and verified route inputs are the critical
dependencies. We now distinguish source announcements from physical-onset
hypotheses, observed playback from simulation, and initial user feedback from
representative validation. Our emphasis has shifted toward a smaller auditable
demonstration with explicit limits rather than an unsupported promise of optimal
routing or automatic traffic control.

### 23. What other issues or comments does your team want to raise?

The prototype recommends rather than actuates. We make no claim of regulatory
approval or production readiness. Aggregate traffic inputs avoid individual
vehicle tracking, but interview materials and future operator audit records
still require privacy review. Before deployment, we would specify access,
security, retention and deletion arrangements, guided by the PCPD's
[data-protection principles](https://www.pcpd.org.hk/english/data_privacy_law/6_data_protection_principles/principles.html),
and obtain advice on applicable operational and electronic-record requirements.
The prototype's approval button is not a claim of legally effective electronic
signature functionality.

GenAI can misread lanes, infer unsupported details and produce unsuitable plans.
Schema checks, source visibility, constraints and human review reduce these
risks but do not eliminate them. We will keep uncertainty visible and test the
console with intended users. We would welcome access to traffic-operations and
transport-modelling expertise to evaluate feasibility beyond the hackathon.
