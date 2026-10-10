# Ripple

An AI incident co-pilot for Hong Kong traffic operators. When an incident is
reported, Ripple reads the Transport Department's message, tests a handful of
response plans in a simulation of the road network, recommends the plan with
the least total delay, and drafts messages that split traffic across the
alternatives instead of sending everyone down the same detour.

**Ripple recommends; it never controls.** Nothing reaches a sign or a signal
until a human operator approves it, and every approval is logged.

Built for the Hong Kong Inter-University GenAI Hackathon for the SDGs 2026
(hack4sdg), Track 1: Green Transport & Smart Mobility. Pilot corridor:
Aberdeen Tunnel and its alternatives. Submission: 18 Oct 2026.

## Tracker

**Last updated: Tue 6 Oct 2026** · Week 3 in progress
· Weekly sync / stand-up: Wednesday afternoon

> **Model decision — Lead, Mon 5 Oct (HKT):** Continue flow-balance SUMO as the
> primary path for a bounded incident P0 diagnostic; keep the simplified model
> available as a contingency. Simulation independently reproduced Data's 96.7%
> GEH<5 count result on the 15 May no-closure hour. Ordinary-morning speed MAPE
> remains 15.7%, above the approximately 15% target, and the speeds are imposed.
> This is a limited count-baseline claim, not acceptance of incident queues,
> recovery or plan benefits. The [decision and next gates](docs/04-plan.md)
> remain separate from incident lane/timing assumptions.

✅ done · 🟡 in progress · ⚪ not started, or nothing in the repo yet

**Critical path:** ✅ demo incident chosen → ⚪ baseline matches reality →
⚪ three plans compared → ⚪ video. If anything slips, cut features and protect
this chain.

> **Keeping this current.** In the same pull request as your work, update your
> rows and add a line to the [update log](#update-log). A status only counts if
> the repo shows it, so link the file that proves it. After each stand-up,
> refresh the date and **This week**. Full timeline:
> [docs/04-plan.md](docs/04-plan.md).

### Milestones

| Date | Milestone | Status |
|---|---|---|
| Sun 27 Sep | 🔒 Lock the primary demo incident and backup | ✅ 28 Sep — Lead selected [IN-26-03365](data/demo_shortlist.md) as primary; IN-26-06391 as backup |
| Sat 3 Oct | 📤 Submit interim report (official deadline Sun 4 Oct) | ✅ Lead confirmed the online form was submitted. The repository keeps the [technical draft](docs/interim-report.md) and [23-question answer bank](docs/interim-report-submission.md); the exact submitted answers and receipt are not archived |
| Mon 5 Oct (HKT) | 🚦 Decide whether to continue with SUMO or use the simplified fallback | ✅ Lead chose conditional SUMO continuation for an incident P0 diagnostic, with fallback retained. Simulation independently reproduced the no-closure count score; speed and incident acceptance remain open ([review](docs/sumo-flow-balance-review-2026-10-05.md), [decision](docs/04-plan.md)) |
| Tue 6 Oct (HKT) | Agree the evidence-labelled P0 setup for IN-26-03365 | 🟡 Data supplied the proposed edge, detector-inferred initial lane and phase times; Simulation's explicit sign-off and the bounded P0 run remain pending ([lane evidence](results/data/closed-lanes_AID01104_20260515-0840_1010.md), [handoff](docs/04-plan.md)) |
| Mon 12 Oct | Pitching workshop, everyone (HKU Innovation Wing 2, 14:00–17:30) | ⚪ |
| Wed 14 Oct | 🔒 **Results freeze**: bug fixes only after this, every number locked | ⚪ |
| Sat 17 Oct | 📤 Submit deck + prototype (official deadline Sun 18 Oct) | ⚪ |
| Thu 22 Oct | Finalists announced | ⚪ |
| Sat 24 Oct | Final pitch, CityU Kowloon Tong | ⚪ |

### Components

| | Component | Owner | Status |
|---|---|---|---|
| A | Loaders: detector and incident archives, live poller | Data | 🟡 Archive client, incident timelines from all three STN files, detector bins on a full 5-minute grid, corridor table, candidate screen against ordinary days, live poller, and the hand-over to the twin (`fetch twin-detectors` → `sim/scenarios/detectors.json`) ([src/loaders/](src/loaders/)). Committed output: [data/detectors.csv](data/detectors.csv), [data/candidates.md](data/candidates.md), [data/demo_shortlist.md](data/demo_shortlist.md). Week 2 checks on the demo morning: usable calibration bins per threshold ([bin survival](results/data/bin-survival_20260515-0755_1035.md)), which lane closed first ([lane by lane](results/data/lane-evidence_AID01104_20260515-0840_0920.md)), and IN-26-03365 re-screened after the 29 Sep screen fixes ([re-check](results/data/candidates_2026-05-15.md)). For the twin: [flow balance](results/data/flow-balance_20260515-0755_0855.md) and [free-flow speeds](results/data/free-flow_20260508_20260424_0730-1100.md) |
| B | Incident Reader (GenAI #1): STN message → `incident.json` | Lead | 🟡 Week 2 evaluation complete on 100 hand-labelled messages. Initial held-out all-field accuracy: citywide **50%**, corridor **75%**. After prompt and label corrections informed by those results, development scores reached 75% and 85%; these are not fresh held-out results. An October prompt experiment performed worse and was not adopted. Output preservation regressions protect evidence ([score history](data/labelled_incidents/LABELLING.md#score-history), [Lead work](docs/2026-10-01-lead-work.md)) |
| C | Twin: SUMO model of the corridor, calibrated to detectors | Simulation | **10 Oct review: NO-GO for public plan comparison by the 14 Oct freeze**, agreeing with Data in [section 4](docs/evaluator-p0-go-no-go-2026-10-09.md). Reconstructed replay inputs match the original P0 sidecar. SUMO 1.27.1 completed bounded independent control and earlier move-over runs: closure GEH remains 82.02% / 267 count bins, and the same wrong-lane teleport persists. Tunnel-side flow, detector placement, imposed incident speeds, recovery assumptions and ramp delay still prevent acceptance. See [technical review and generated run artifacts](docs/simulation-evaluator-review-2026-10-09.md). |
| D | Plan Generator (GenAI #2): 3–5 plans + constraint validator | Lead | 🟡 P0/P1/P2 generation, schema checks and all five documented constraints are implemented with offline tests. A model-free `--check-only` path now validates the incident/context handoff before generation. Real-model quality and reviewed C/E routes, demand and controls remain outstanding ([handoff](docs/lead-pipeline-handoff.md)) |
| E | Evaluator: runs every plan, writes metrics to `results/` | Data | 🟡 No `src/evaluator/` implementation or real P0/P1/P2 results are on main yet. [PR #35](https://github.com/f1ymango/ripple/pull/35) was closed as superseded; its older fallback calibration was not accepted. [PR #46](https://github.com/f1ymango/ripple/pull/46) revises the no-closure inputs but is still under review, not an evaluator result. E must write comparable contracted results and provenance sidecars before F/G can recommend a plan; compliance/clearance sensitivity remains outstanding ([handoff](docs/lead-pipeline-handoff.md)) |
| F | Briefing Writer (GenAI #3): briefing + bilingual sign text | Lead | 🟡 Bilingual drafting, saved-result selection, metric-token insertion, provenance verification and VMS limits are implemented with offline tests. A model-free handoff check revalidates plans and comparable results before an LLM call. Real validated E results and human language review remain outstanding ([handoff](docs/lead-pipeline-handoff.md), [Lead next steps](docs/2026-10-03-lead-next-steps.md)) |
| G | Operator console: map, plan comparison, Approve + audit log | Visuals | 🟡 [PR #41](https://github.com/f1ymango/ripple/pull/41) merged 4 Oct after Lead review: the console has the 28-detector map and archived incident playback plus provenance-checked plan comparisons, matching bilingual briefings and identified operator decisions with cross-platform audit locking. Real accepted plan outputs and an end-to-end operator review are still missing. Trajectory replay remains deferred until C/E can bind FCD output to evaluated runs ([operator integration](src/console/OPERATOR_WORKFLOW.md)). |
| H | Evidence pack: validation, accuracy, interviews, deck | Impact | 🟡 Interim form submitted. Repository evidence includes sourced problem research, one qualitative [minibus-driver interview](evidence/interviews/2026-09-26-minibus-driver.md), the [technical draft](docs/interim-report.md) and [answer bank](docs/interim-report-submission.md). Additional interviews, accepted validation/results, deck and video evidence remain outstanding |

The JSON contracts between modules are in
[docs/03-architecture.md](docs/03-architecture.md). Build to them.

### Week 3 priorities (5–11 Oct)

| Owner | Deliverable | Next evidence |
|---|---|---|
| Data + Simulation | Confirm Data's evidence-labelled incident setup; attempt a bounded P0 diagnostic by 7 Oct while Data builds E | 🟡 Data proposed edge `44419212`, the detector-inferred initial slow lane, assumed 08:55 onset, and TD-reported 09:36/10:02 phase times. Simulation's explicit acceptance remains pending. Neither incident queues nor plan effects are validated; E and contracted results are still missing from main ([lane evidence](results/data/closed-lanes_AID01104_20260515-0840_1010.md), [handoff](docs/04-plan.md)) |
| Lead | Hold conditional SUMO decision and validate C/E context and real D/F handoffs | 🟡 Model route decided for the bounded P0 step, with fallback retained. Reader evaluation, interim submission and model-free D/F checks are complete. Reviewed context, real plan quality, comparable results and bilingual briefing remain unverified ([decision](docs/04-plan.md), [handoff](docs/lead-pipeline-handoff.md)) |
| Visuals | Connect the merged comparison and briefing workflow to accepted outputs | 🟡 [PR #41](https://github.com/f1ymango/ripple/pull/41) merged with green Linux and Windows checks. The observed playback remains available; trajectory replay awaits C/E output provenance and real operator review ([operator integration](src/console/OPERATOR_WORKFLOW.md)) |
| Impact | Continue interviews and build the final evidence pack and deck | 🟡 Interim form submitted 3 Oct; additional interviews, validated results and final impact claims remain open ([interim draft](docs/interim-report.md)) |

### Week 1 outcomes (21–27 Sep)

| Owner | Task | Done when | Status |
|---|---|---|---|
| Lead | Freeze scope; write `CLAUDE.md`; create repo; test the Incident Reader on 20 real messages | repo exists, 20 messages parsed | ✅ 22 Sep |
| Data | Pull Aberdeen detector + incident archives; shortlist 3–5 corridor incidents with good detector coverage | shortlist in `data/candidates.md` | ✅ 26 Sep — all 35 corridor accidents of 22 Mar–21 Sep checked against ordinary days ([data/candidates.md](data/candidates.md)); Data's pick of five, headed by IN-26-03365, with reasons and replay windows ([data/demo_shortlist.md](data/demo_shortlist.md)) |
| Visuals | Map of corridor detectors coloured by speed, from a static file | screenshot posted | ✅ 24 Sep — [screenshot](docs/img/week1-corridor-map.png) of the 21 Sep 08:20 bin ([src/console/app.py](src/console/app.py)) |
| Simulation | Install SUMO; build the Aberdeen network from OSM; get vehicles moving | a video of cars moving | 🟡 SUMO and a draft network run locally; record/share evidence and improve route coverage ([guide](src/twin/README.md)) |
| Impact | Line up 2–3 user interviews; fact-check the evidence claims; start the interim report | Interview notes, sourced problem claims, and an interim report outline | 🟡 one [minibus-driver interview](evidence/interviews/2026-09-26-minibus-driver.md) completed on 26 Sep; problem claims revised with direct sources in [docs/05-pitch.md](docs/05-pitch.md); [interim report](docs/interim-report.md) remains an outline |

### Integration status

The console framing, theme and playback control fixes are merged in
[PR #31](https://github.com/f1ymango/ripple/pull/31), with a
[Visuals handover](docs/visuals-handover.md) saved for the next session. The
console playback (PR #29), Component C source audits (PR #30), and Data's
[week 2 checks (PR #32)](https://github.com/f1ymango/ripple/pull/32) are merged.
The operator workflow is merged in [PR #41](https://github.com/f1ymango/ripple/pull/41).
The provisional October replay inputs are archived in
[results/twin/oct04-provisional-replay-inputs.zip](results/twin/oct04-provisional-replay-inputs.zip),
but the standalone network and E1 loops are not reviewed releases.

### Current handoffs and open decisions

- **Who runs the live poller, and on which machine.** Its data has no gaps,
  but it only records while it runs (`python -m src.loaders.fetch live`).
- **What the Evaluator (E) simulates for `lanes_closed: ["unspecified"]`.**
  Data proposed a case-specific rule for `IN-26-03365`: infer the initial slow
  lane from five successive archived AID01104 readings from 08:54–09:00 with
  no slow-lane vehicles while the fast lane carried traffic. This is an
  assumption, not confirmation of the physical lane; AID01105 was unavailable
  that morning ([lane evidence](results/data/closed-lanes_AID01104_20260515-0840_1010.md)).
  Simulation's explicit sign-off on this rule is pending. A general default
  lane and no-evidence behaviour for other incidents are still unagreed.
  Data also proposed an **assumed** 08:55 physical onset. TD first reported
  partial closure at 09:01, all lanes at 09:36 and incident end at 10:02;
  the latter two are observed *report times*, not observed physical transition
  times. E must disclose the scenario assumptions and sources with its results.
  No operator action can precede the relevant report
  ([docs/03-architecture.md](docs/03-architecture.md) §3). The pre-incident
  GEH target ends at 08:55, before TD's first report.
- **Calibration thresholds** (Data + Simulation): a bin is used for GEH only at
  ≥ 40% archive coverage and ≥ 90% of lane readings valid
  ([docs/02-data.md](docs/02-data.md) §7). Relax them deliberately if too few
  bins survive, and state the values on the validation slide. *29 Sep, for
  15 May before 08:55:* 242 of 336 bins at 40% / 90%, 298 at 20% / 90%; 75% instead
  of 90% for lane readings changes nothing; low- and high-coverage bins differ by
  0.2 km/h in mean speed, so the filter trades precision, not bias
  ([bin survival](results/data/bin-survival_20260515-0755_1035.md)).
- **`network_state.json` vs what A hands the twin**: A now writes the twin's
  own input, `sim/scenarios/detectors.json`, one row per 5-minute slot
  (`python -m src.loaders.fetch twin-detectors`, as the Lead suggested on
  26 Sep). The contract in [docs/03-architecture.md](docs/03-architecture.md)
  still shows `network_state.json`: update it or drop it (Lead + Simulation).
- **Enter the Best WorkBuddy Award?** If yes, assign one person in week 3
  ([docs/01-hackathon.md](docs/01-hackathon.md) §5).

### Known issues

- [data/candidates.md](data/candidates.md) was generated before the 29 Sep
  screen fixes (public holidays were accepted as ordinary days; control days
  before `--start` were never checked for incidents) and the 30 Sep addition
  of Stubbs Road to corridor screening. The demo incident was re-checked and
  unchanged under the first two fixes ([re-check](results/data/candidates_2026-05-15.md)),
  but that one-day re-check also predates the Stubbs Road change. Regenerate
  the relevant screen before relying on any ranking or control-day claim
  ([notes](docs/notes-from-data.md)).
- Incident Reader errors left in v2
  ([LABELLING.md](data/labelled_incidents/LABELLING.md#score-history)): one
  named lane closed with "only remaining lanes are" (plural) gets
  `lanes_total` 2, which the message does not say (7 of 100); a road junction
  ("the junction of X and Y") becomes road X; `near_landmark` filled where the
  message has no "near" (7 of 100). Found on the gold set, so fixing them in
  the prompt needs a fresh set to measure the result.
- The historical archive serves only about half the raw detector snapshots it
  lists (39% were a persistent 404 on 21 Sep), so a 5-minute bin usually holds
  1–3 observed minutes. Summing raw volume into a bin would understate flow by
  about half, so the loader reports a flow rate and a `coverage_pct` instead.
  The missing minutes cannot be recovered
  ([docs/02-data.md](docs/02-data.md) §3, §7).
- For [C], the standalone draft network and E1 loops are **not reviewed**;
  provisional replay inputs are committed as an
  [archive](results/twin/oct04-provisional-replay-inputs.zip). The earlier
  September run stopped at 6,410 of 30,900 seconds with zero scoreable bins.
  A historical May 15 pre-incident replay completed 4,500 s:
  66.5% of 242 count bins meet GEH<5, speed MAPE is 36.9% over 296 bins, and
  the run ends with 2,405 waiting vehicles and 68 teleports. Even quarter-volume
  demand still produced 9 teleports, so demand volume is not the only unresolved
  factor. The offline audit now checks all 24 directed corridor links: all are
  reachable, and route distances are 0.959-1.120 times direct distance on the main
  chains and 1.002-1.093 times on the western alternative. This checks locality; it
  does not make the network reviewed or validate incident behavior. This older
  diagnostic is superseded as current no-closure count evidence by the
  independent 5 Oct review above; it remains useful history. Keep the
  simplified fallback available as a contingency, not as an accepted model.
- For [C], the mapper now uses detector chains and source road names to
  reject opposite-direction and wrong-road nearest-edge matches. OSM aliases
  are accepted only when the cached feed's lane count supports the candidate;
  nearby same-name edges use lane count only as a tie-break. The old AID01106
  surface-road selection forced a 1.77 km route to AID01107 despite 458 m
  between their registry coordinates. The source-matched tunnel approach is
  442 m along the SUMO route. AID01214 now matches three TD lanes, and
  AID01218's tunnel-exit edge is pinned to the exact network and registry
  hashes. Three lane counts still differ between OSM and TD; three more
  detectors have no lane observations in the cached window. See the generated
  [OSM audit](results/twin/osm-network-audit.md) and [mapping review](results/twin/detector-map-review.md).
  The draft remains unapproved and has no new traffic validation.
- For [C], the demand fitter now refuses a calibration window that extends
  into the configured incident, and the SUMO runner checks its edge, selected
  lane indices, and incident horizon before starting. It can model ordered
  closure phases, including escalation to all lanes. This prevents an invalid
  scenario from silently becoming a lane-0 closure. It does not choose a lane
  for the incident's initial "part of the lanes" period; that remains an
  explicit scenario decision.
- For [C]: the processed segment-speed feed is fully retrievable. It has no
  volume, so it cannot support GEH, but it is the better series for the speed
  side of validation ([docs/02-data.md](docs/02-data.md) §3).

### Definition of done

- [ ] One real archived incident replayed end to end
- [ ] Validation chart: simulated vs observed, with a stated error
- [ ] Three plans compared on ≥ 4 metrics
- [ ] Sensitivity: plan still wins across compliance and clearance ranges
- [x] Incident Reader accuracy measured on ~100 labelled messages
- [ ] One on-screen moment where a real bilingual message goes in and a ranked
      plan + briefing + sign text come out
- [ ] Operator console with an Approve action and an audit log
- [ ] 2–3 user interviews recorded in `evidence/interviews/`
- [ ] ~90-second video
- [ ] Deck covering all five criteria
- [ ] Every number traceable to a file in `results/`

### Update log

Newest first. One line per change that matters, with a link to the proof.

**Tue 6 Oct**
- Data proposed a case-specific P0 setup for IN-26-03365 using the revised
  inputs under review in [PR #46](https://github.com/f1ymango/ripple/pull/46).
  Detector evidence supports an inferred initial slow lane, while 08:55 and
  the physical transition times remain assumptions; Simulation's explicit
  agreement and a bounded P0 result are still pending
  ([lane evidence](results/data/closed-lanes_AID01104_20260515-0840_1010.md),
  [decision gates](docs/04-plan.md)).
- Verified [PR #35](https://github.com/f1ymango/ripple/pull/35) is closed
  without merge; the simplified fallback remains an unvalidated contingency.

**Mon 5 Oct**
- Lead chose conditional SUMO continuation for a bounded incident P0 diagnostic,
  keeping the simplified model available. Simulation independently reproduced
  the 15 May no-closure 96.7% GEH<5 / 15.7% speed MAPE result; removing speed
  signs left counts at 96.7% but raised speed error to 41.2%. Incident and plan
  benefit claims remain blocked ([review](docs/sumo-flow-balance-review-2026-10-05.md),
  [decision](docs/04-plan.md)).

**Sun 4 Oct**
- Data's merged [flow-balance report](docs/sumo-flow-balance-2026-10-04.md)
  reports a provisional 96.7% GEH<5 and 15.7% speed MAPE on the 15 May
  no-closure hour, with 97.5% / 13.2% under a distinct within-day refresh.
  Simulation review and incident validation remain open. The Component C and E
  tracker rows now reflect this evidence and the missing evaluator/results.
- Lead reviewed and merged [Visuals' operator workflow (PR #41)](https://github.com/f1ymango/ripple/pull/41):
  provenance-checked comparisons, matching briefings and cross-platform audit
  actions. The focused local Windows suite passed 64 tests; PR CI passed 434
  Linux and 64 Windows tests. Real accepted results and an end-to-end operator
  review remain outstanding.
- Lead deferred the SUMO/fallback decision to Mon 5 Oct evening (HKT) to allow
  one more calibration pass. Roughly 80% GEH<5 is a progress marker, not the
  documented ≥85% GEH and ~≤15% speed acceptance gate; both candidate models
  still need comparable no-closure evidence ([plan](docs/04-plan.md)).

**Sat 3 Oct**
- Lead confirmed the interim form was submitted. The repository retains the
  [technical draft](docs/interim-report.md) and
  [23-question answer bank](docs/interim-report-submission.md), but not the exact
  submitted answers or receipt.
- Lead completed the evidence review of merged and open contributions. The
  4 October priority is a SUMO/fallback decision using comparable no-closure
  diagnostics; neither model is accepted yet
  ([status review](docs/project-status-2026-10-03.md)).
- Lead added model-free checks for the D/F handoffs, revalidation of plans before
  briefing, and the binary-open hygiene-check correction. The full Windows
  Python 3.13 suite passed: 383 tests, with one Altair deprecation warning
  ([handoff](docs/lead-pipeline-handoff.md),
  [next steps](docs/2026-10-03-lead-next-steps.md)).

**Wed 30 Sep**
- Lead: added approved E/F result-provenance sidecars, rejected zero-second
  signal actions and common worded numeric claims. Saved copy-ready
  [team follow-up notes](docs/2026-09-30-lead-follow-up.md), including the
  fallback PR review and outstanding validation decisions.
- Lead: added the verified Reader contribution to the [interim report](docs/interim-report.md)
  and the initial D/F command-line path with offline tests and a
  [C/E handoff guide](docs/lead-pipeline-handoff.md). No real plan benefits are claimed.
- Lead: the Reader now imports the shared `CORRIDOR_ROAD_NAMES` from
  [src/loaders/corridor.py](src/loaders/corridor.py). Stubbs Road stays in scope
  as the over-hill alternative in [docs/02-data.md](docs/02-data.md) §5, and
  the loaders' incident screen now catches it too. The duplicate road list
  and its open decision are closed ([Data handoff](docs/notes-from-data.md)).
- Component A, for the 66.5% GEH / 36.9% MAPE diagnostic: 57 of its 81 failing
  count bins are at six detectors where the twin carries 33–61% of the observed
  traffic, each just after a stretch where traffic joins the corridor. New
  `fetch flow-balance` measures those joins and exits between neighbouring
  detectors on 15 May and two ordinary Fridays (e.g. +646 veh/h between AID01216
  and the westbound tunnel), and `fetch free-flow` measures light-traffic speeds
  per detector: the median driver beats the twin's 60 km/h cap at 14 of 25
  ([flow balance](results/data/flow-balance_20260515-0755_0855.md),
  [free-flow](results/data/free-flow_20260508_20260424_0730-1100.md),
  suggestions for Simulation in [docs/notes-from-data.md](docs/notes-from-data.md)).

**Tue 29 Sep**
- Component G: follow-up on `visuals/console-framing-theme` fits the map
  to the detector bounds, keeping all 28 detector circles inside the frame at
  1280px and 1500px browser widths. A shared light theme with blue controls makes
  screenshots consistent under light and dark browser preferences; the tab and
  page titles now match. Fixed a playback bug found in the browser: pausing,
  stepping, rewinding or scrubbing now immediately restores the Play button.
  All 38 console tests passed, including regressions for the button state and
  stepping after scrubbing. Playwright checked the two widths, the theme,
  scrubbing to the real 09:15
  incident bin, and playback advancing and pausing.
  ([screenshot](docs/img/console-framing-theme.png),
  [src/console/app.py](src/console/app.py),
  [.streamlit/config.toml](.streamlit/config.toml))
- Lead: checked the two archived messages for `IN-26-03365` with `qwen3:8b`
  (seed 42). Both parsed and matched the expected road, direction, landmark,
  incident type, timestamps, and lane scope (`["unspecified"]` then `["all"]`).
  TD announced them at 09:01 and 09:36; the first archived copies were at
  09:07 and 09:43. The first `notes` incorrectly says the road name includes
  the direction bracket, although the structured fields separate them correctly.
  This two-message check is not a new accuracy score
  ([source messages](data/demo_incident_messages.jsonl),
  [run](results/reader/2026-09-29T1608_qwen3-8b.jsonl),
  [LLM log](evidence/ai-log/2026-09-29.jsonl)).
- Tracker: reconciled the component, interview, and PR status with the merged console playback and Component C audits. The baseline is still unvalidated and the interim report remains an outline ([playback](docs/img/week2-incident-playback.png), [lane-scope cross-check](results/twin/may14-lane-scope-crosscheck.md), [interim outline](docs/interim-report.md)).
- Component A: fixed two bugs in the candidate screen: public holidays counted
  as ordinary days (IN-26-03365 was compared with Labour Day, 1 May), and control
  days before `--start` were never checked for incidents. IN-26-03365 re-screened
  under both fixes: ordinary days now 8 May and 24 Apr, same five detectors
  credited, score 4.38 ([re-check](results/data/candidates_2026-05-15.md)). New
  demo-morning checks: usable calibration bins per threshold
  ([bin survival](results/data/bin-survival_20260515-0755_1035.md)) and
  lane-level evidence supporting Data's slow-lane proposal
  ([lane by lane](results/data/lane-evidence_AID01104_20260515-0840_0920.md)).
  One shared corridor road list, `CORRIDOR_ROAD_NAMES`
  ([corridor.py](src/loaders/corridor.py)). Notes for the Lead and Simulation:
  [docs/notes-from-data.md](docs/notes-from-data.md).

**Mon 28 Sep**
- Component C: refreshed the May 15 hand-over from the official HK traffic archive (80 of 113 listed snapshots served; 28 detectors, 32 five-minute slots; 600 count-and-speed pairs) and regenerated the source-hashed OSM audit. The observations reproduce the same six unresolved lane scopes; no placement or calibration claim changed ([audit](results/twin/osm-network-audit.json)).
- Component C: added a source-hashed cross-day lane-scope auditor and checked three OSM/TD lane-count conflicts against six listed May 14 archive snapshots using the TD parser. AID01221 and AID01222 report three lane labels in 12 observed periods; TDSAPR10001 reports three in 8. This separate-day evidence corroborates feed scope but does not establish placement. Three detectors were absent from selected snapshots, so those gaps remain open ([auditor](src/twin/audit_lane_scope.py), [cross-check](results/twin/may14-lane-scope-crosscheck.md)).
- Component C: reran the offline OSM/TD audit from the local May 15 cache and draft SUMO network; it reproduced 24/24 reachable directed links, with six lane-scope gaps unresolved. No network geometry, lane tags, observations, or simulation outputs changed.
- Component G: the console plays an archived window back bin by bin — transport
  controls, a scrubbable slider, and a timeline strip of the slowest corridor
  detector with TD's own reported/cleared times on it. The map now has three
  states rather than two: a loop that reported and counted nobody is the
  closure, and is no longer drawn in the same grey as a reading the archive
  never served. On IN-26-03365 (Fri 15 May) AID01101–04 fall from ~65 km/h to
  3–8 km/h from 08:55 and AID01104's loops report an empty road at 09:15–09:25,
  while the corridor *mean* moves by about 2 km/h — which is why the strip
  tracks the slowest detector and not the mean.
  ([screenshot](docs/img/week2-incident-playback.png), [src/console/app.py](src/console/app.py))
- Component C: extended the offline source-backed network audit to include all six directed links on the western alternative. The 24 main and alternative links are reachable in the local OSM network, with modeled path distance at most 1.12 times registry-coordinate distance. Centralized the two western travel orders so detector direction matching, route generation, and audit use the same chains. No OSM tags, geometry, lane counts, or traffic observations changed; the local network and E1 files remain unreviewed. Ten focused Component C tests passed. ([audit](results/twin/osm-network-audit.md), [pre-incident diagnostic](results/twin/may15-preincident-diagnostic.md))

**Sun 27 Sep**
- Component C: added fail-fast checks before demand fitting and SUMO launch.
  The fitter verifies its duration fits before incident onset; the runner
  verifies the closure edge and lane indices against the local network and
  supports ordered lane-closure phases and requires the full closure to fit
  the configured run horizon. An unspecified lane selection is never
  converted to lane 0. No simulation was launched in this change; the initial
  partial-closure lane still needs an explicit, source-backed scenario choice.
- Component C: audited 28 detector placements against 66 cached May 15 raw
  snapshots and the exact local OSM/SUMO hashes. Used OSM's English street-name
  aliases only when the same-window TD lane count corroborates the edge. The
  AID01106-to-AID01107 position-aware route fell from 1,771.83 m to 441.79 m;
  AID01214 now maps to a three-lane flyover edge, and AID01218 is pinned to a
  two-lane tunnel-exit edge for the current network/registry hashes. Three lane
  mismatches, three detectors without usable lane records, and an endpoint
  offset at AID01106 remain visible in the audit. No OSM tags or geometry were
  edited, no simulation was rerun, and the local network remains provisional
  ([audit](results/twin/osm-network-audit.md),
  [placement review](results/twin/detector-map-review.md)).
- Tracker: clarified the Week 2 Lead task as Reader verification and contract
  handoff; Data/E owns the `unspecified` lane assumption, and Simulation/C
  owns physical edge mapping ([docs/04-plan.md](docs/04-plan.md),
  [docs/03-architecture.md](docs/03-architecture.md)).
- Lead: selected `IN-26-03365` as the primary demo incident and
  `IN-26-06391` as backup from Data's five-candidate shortlist. The initial
  lane and affected simulation edge still need an explicit modelling decision;
  selection is not baseline validation
  ([data/demo_shortlist.md](data/demo_shortlist.md)).

**Sat 26 Sep**
- Component C: rebuilt the draft SUMO network from the cached OSM extract with left-hand traffic and street names; detector placement now uses repository detector chains, source road names, and edge direction. Rechecked the ten flagged placements and regenerated local per-lane loops. This fixes several wrong-road candidates, including AID01104. Raw-feed/OSM lane-count mismatches and the 3.6x AID01106-to-AID01107 path remain unresolved; no road geometry or lane counts were fabricated or edited, and the network is still provisional ([map review](results/twin/detector-map-review.md)).
- Component C: pulled the latest `main` (PR #19 was already an ancestor of this
  branch). Rebuilt the May 15 07:55–10:35 detector hand-over from the raw cache:
  80 snapshots parsed, 896 detector slots, 600 with both count and speed. The
  archive index endpoint was unreachable, so this uses only cached snapshots
  and does not claim complete archive coverage. Replaced the obsolete Sep 3
  calibration window with the May incident grid. Confirmed AID01104 on the
  eastbound flyover; made provisional local placements for the other nine
  flagged detectors and regenerated per-lane loops. OSM-name/offset conflicts
  are documented, and the draft network remains unreviewed; no new full
  simulation validation was run ([sim/scenarios/calibration.json](sim/scenarios/calibration.json),
  [results/twin/detector-map-review.md](results/twin/detector-map-review.md),
  [src/twin/](src/twin/)).
- Data: demo incident shortlist. The candidate screen was rebuilt: every
  corridor accident is compared with two ordinary days (same weekday and time,
  no corridor incident), and a detector counts only if it ran 20+ km/h slower
  for longer than two ordinary days ever differ. Picking the worst 5-minute
  bin had let one noisy detector "win" 8 of 22. Five proposed, headed by
  IN-26-03365, with what each shows and how to replay it
  ([data/demo_shortlist.md](data/demo_shortlist.md),
  [data/candidates.md](data/candidates.md)).
- Data → Simulation hand-over, from the Lead's review: detector bins now come
  on a full 5-minute grid (an empty slot is a row, never a gap), and
  `fetch twin-detectors` writes `sim/scenarios/detectors.json` with one
  observation per slot and `null` where a count or speed is missing or
  unusable. Checked through the twin's own `evaluate.py` (timestamps keep a
  missing interval from shifting later comparisons) and `place_detectors.py`.
  The direction fix reads `data/detectors.csv` because
  the export intentionally omits map metadata. 266 tests
  ([src/loaders/twin_export.py](src/loaders/twin_export.py),
  [tests/test_twin_bridge.py](tests/test_twin_bridge.py)).
- Component C follow-up: detector direction and leg metadata drive placement
  and route chains, all lanes are measured, demand uses the first calibration
  hour, and zero-count bins remain scoreable without a speed. The 15 May replay
  begins at the measured 08:55 queue onset with 15 minutes of warm-up. The
  pre-incident diagnostic records 66.5% GEH<5 and 36.9% speed MAPE; it is not a
  validated incident baseline. The OSM network remains provisional
  ([results/twin/](results/twin/)).
- Lead: repo hygiene and CI. `pandas` moves to 2.3.3, which has a Python 3.14
  build, so `pip install -r requirements.txt` works on 3.14 and that known
  issue is gone. A `.gitattributes` decides line endings for everyone instead
  of leaving them to each machine's Git installer. GitHub Actions runs the
  suite on every push and pull request, so the Lead is no longer the only
  thing that runs the tests
  ([.github/workflows/tests.yml](.github/workflows/tests.yml)). A new
  [tests/test_repo_hygiene.py](tests/test_repo_hygiene.py) fails if any text
  file in `src/` is opened without an explicit encoding, which is the cp1252
  trap the rules below warn about. 268 tests.

**Fri 25 Sep (afternoon)**
- Twin validation fix: `evaluate` read `meanSpeed`, which SUMO's loop output does not have, so every
  simulated speed was 0 and the speed error 100% on every bin. It now reads `speed` (checked against
  SUMO's own `det_e1_file.xsd`) and leaves out bins where no vehicle was measured
  ([src/twin/evaluate.py](src/twin/evaluate.py), [tests/test_twin.py](tests/test_twin.py)).
- The twin (component C) has code: SUMO setup scripts from Simulation (#12),
  moved into the repo layout — scripts in [src/twin/](src/twin/README.md),
  run from the repo root as `python -m src.twin.<script>`. The network and
  loops referenced by the old update were not present on this branch; the new
  OSM build is an unreviewed local draft, and generated files stay under the
  git-ignored `sim/work/`.
- Interview plan: three target profiles, first interview scheduled for
  Sat 26 Sep 15:00 ([evidence/interviews/plan.md](evidence/interviews/plan.md), #13).
- Incident Reader accuracy merged (#14).
- Evidence fact-check: every claim in [docs/05-pitch.md](docs/05-pitch.md) §3 is tagged with its source and the date it was checked (#15). 8 of the 15 sources are a homepage or listing and should point at the page that holds the figure. Interim report skeleton added ([docs/interim-report.md](docs/interim-report.md), #16).
- Housekeeping: every branch whose pull request is merged was deleted from
  the remote.

**Fri 25 Sep**
- Data layer: the incident loader reads all three Special Traffic News files
  (English, Traditional and Simplified Chinese). Each archived copy of the
  feed holds one message, and the archive saves the three files at different
  moments, so the Chinese files catch messages and closures the English one
  missed. Over 22 Mar–21 Sep: complete timelines 68% → 85% of incidents;
  corridor accidents with a complete timeline 35 → 49 of 55, and ≥ 20 min
  22 → 35. Audited for contradictions: no two copies of a message disagree on
  incident number or time, no start time moves, and all 22 earlier usable
  accidents keep the same start and end. Two rules the extra data exposed: the
  start is the message published as NEW even after TD switches it to CLOSED,
  and a clearance is read only from an incident's latest message
  ([src/loaders/incidents.py](src/loaders/incidents.py),
  [docs/02-data.md](docs/02-data.md) §2).
- Data layer: incident timelines fixed. TD closes an incident by switching
  an existing message to CLOSED, and the loader kept each message only as
  first seen, so most closures were lost; that is where "only a quarter have
  a CLOSED" came from. Over six months (22 Mar–21 Sep, 18,381 STN snapshots)
  68% of all incidents now have a complete timeline, and 35 of the 53
  corridor accidents do. Also: 4 archive snapshots padded with NUL bytes are
  now read rather than skipped (the 4 truly truncated ones are still skipped,
  as in #10), and version listings are paged a month at a time to stay under
  the archive's 10,000-row cap
  ([src/loaders/incidents.py](src/loaders/incidents.py),
  [docs/02-data.md](docs/02-data.md) §2, §3).
- Incident Reader accuracy measured on the 100 hand-labelled gold messages.
  **v1, held out:** all fields right on 50% citywide (95% CI 39–61%) and 75%
  on the corridor (53–89%); by field, 90–99% except direction at 73%.
  **v2**, after one prompt fix and four label corrections made once v1 had
  been seen: 75% citywide (65–83%), 85% corridor (64–95%). Quote v2 only next
  to v1 ([LABELLING.md, Score history](data/labelled_incidents/LABELLING.md#score-history),
  [results/reader/](results/reader/)).
- Why v1's direction was low: the 24 Sep prompt's road_name example dropped
  "(Kowloon bound)" without saying where it goes, and the model learned to
  drop `bound` from directions. Visible on the dev set (`<place> bound`
  directions 18/18 → 12/18) and fixed there (back to 18/18); on the gold set
  the fix alone takes citywide
  from 40 to 59 of 80 ([src/reader/prompts/system.md](src/reader/prompts/system.md)).
- Before any score was seen, a rule-based check of every label against its
  message text and the guide led to 55 approved corrections to 54 labels, 40
  of them re-opened messages labelled with the lane that had been closed. The
  first hand-labelled pass is commit 459cfe8; the labels as scored for v1 are
  in [data/labelled_incidents/history/](data/labelled_incidents/history/).
  The v1 run started once every message had a first-pass label, while that
  check was under way; only its summary line was read before the score
  ([LABELLING.md](data/labelled_incidents/LABELLING.md#score-history) gives
  the order of events).
- Every corridor message in the gold set (20) has now been through a live
  model run; none was flagged.

**Thu 24 Sep**
- Week-1 Visuals task done: the corridor map, coloured by speed, screenshot
  posted ([docs/img/week1-corridor-map.png](docs/img/week1-corridor-map.png)).
  The frame is the 21 Sep 08:20 bin — mean 55 km/h, 5 of 28 detectors at or
  below 30 km/h, slowest AID01106 at 14 km/h. The morning peak clears by 08:45,
  so the later bins show nothing.
- Console: the bin slider showed a full ISO timestamp
  (`2026-09-21T08:20:00+08:00`) on every tick; it now shows clock time. Also
  landed: headline stats, colour legend, street basemap, a readable snapshot
  picker, and fixes for a blank-speed snapshot crashing the page, a bin width
  labelled 5 minutes whatever the data said, and the coverage-filtered exports
  being indistinguishable from full windows
  ([src/console/app.py](src/console/app.py), 17 tests in
  [tests/test_console.py](tests/test_console.py)).
- Data layer: a truncated archive snapshot no longer crashes `fetch incidents`,
  `candidates` or `detectors`. Any snapshot that does not parse is skipped, and
  each run prints how many snapshots were listed, read, not served and
  unparseable, naming the unparseable ones. Across 22 Jun–21 Sep only one of
  9,690 STN snapshots is affected, 3 Aug 08:15. The archive returns the same
  cut-off file on every request, so refetching cannot fix it
  ([src/loaders/incidents.py](src/loaders/incidents.py),
  [tests/test_loaders_edges.py](tests/test_loaders_edges.py),
  [docs/02-data.md](docs/02-data.md) §3).
- Contract change agreed by the team: `lanes_closed` gains `unspecified` for
  "part of the lanes is closed", which had come out the same as "no lane
  closed". The Evaluator (E) decides what to simulate for it
  ([docs/03-architecture.md](docs/03-architecture.md) §3,
  [src/reader/incident.schema.json](src/reader/incident.schema.json),
  [src/reader/prompts/system.md](src/reader/prompts/system.md)).
- Incident Reader accuracy, set up: the sampler draws a gold set of 80
  citywide + 20 corridor messages from 22 Jun–21 Sep, leaving out the dev set
  and the prompt's worked examples; a Streamlit app to label them; a scorer
  with per-field accuracy and 95% intervals, its matching rules fixed before
  any score is seen ([LABELLING.md](data/labelled_incidents/LABELLING.md),
  [src/reader/label.py](src/reader/label.py), [src/reader/score.py](src/reader/score.py)).
  The sampler now reads the data layer's cache and still rebuilds the dev set
  byte for byte.
- Gold set drawn: 80 citywide + 20 corridor messages from 2,519 incidents,
  with no dev-set incident or worked example among them. 47 of the 100 say
  "part of the lanes"
  ([data/labelled_incidents/gold_messages.jsonl](data/labelled_incidents/gold_messages.jsonl)).
- Reader prompt and labelling guide aligned on four rules found by labelling
  the dev set twice: a closure that also mentions buses takes the closure's
  cause, not `public_transport_notice` (otherwise code marks a corridor
  closure out of scope); "road incident" alone is `other`; a bracketed
  section name stays in `road_name`; English wins over Chinese. On the dev
  set the Reader parses 20/20 and gives `unspecified` for all 7 "part of the
  lanes" closures, but still types "road incident" as `road_works`
  ([results/reader/2026-09-24T1504_qwen3-8b.jsonl](results/reader/2026-09-24T1504_qwen3-8b.jsonl)).
- One archived STN snapshot (3 Aug 08:15) is truncated. The gold sampler skips
  and reports it. The data layer's incident loader crashed on it, which
  blocked the candidate screen over 22 Jun–21 Sep; fixed in the entry above.

**Wed 23 Sep**
- Evidence pack (component H): workspaces for the interviews and the deck, each
  with its own definition of done ([evidence/interviews/](evidence/interviews/),
  [deck/](deck/)).
- Operator console (component G) started: Streamlit app with the 28-detector
  corridor map coloured by speed, greying detectors when no speed snapshot is
  loaded rather than inventing one ([src/console/app.py](src/console/app.py)).
- All 15 items from the PR #2 review of the data layer fixed, each with a test
  that fails on the previous code. The ones that changed numbers: an offline
  lane halved a detector's count, and sensor outages were reported as archive
  gaps. Also fixed: a 15-minute request returned 20 minutes, and censored
  incidents showed a duration of 0. 153 tests
  ([tests/test_loaders.py](tests/test_loaders.py),
  [tests/test_loaders_edges.py](tests/test_loaders_edges.py)).
- Found in the detector feed: when no vehicle passes, the speed is the road's
  speed limit (about 19% of lane readings) and occupancy is often -1. Such a lane
  now has no speed and 0% occupancy. At night 77 of 975 corridor bins had been
  showing the limit as a measured speed ([docs/02-data.md](docs/02-data.md) §1).
- Lane convention agreed: offside to nearside Fast, Middle Lane 2, Middle
  Lane 1, Slow ([docs/03-architecture.md](docs/03-architecture.md) §3). The
  Incident Reader prompt already matches.
- Ways around the archive's missing minutes: the candidate screener scores
  coverage, `--bin-minutes 15` for calibration, and a live poller
  ([src/loaders/candidates.py](src/loaders/candidates.py),
  [src/loaders/live.py](src/loaders/live.py)).
- Tracker and `CLAUDE.md` brought up to date with the data layer
  ([#3](https://github.com/f1ymango/ripple/pull/3)).

**Tue 22 Sep**
- Data layer (component A): archive client, incident timelines from archived
  STN snapshots, detector readings in 5-minute bins with coverage, and the 28
  corridor detectors ([data/detectors.csv](data/detectors.csv), for the map).
  Merged in PR #2.
- Measured against the live feed: `lane_id` and `direction` are text, the
  archive timestamp runs about 9 minutes behind the data, and about half of the
  listed detector snapshots are a persistent 404
  ([docs/02-data.md](docs/02-data.md)).
- Incident Reader pinned to `qwen3:8b`. After the fix below, both models
  parse 20/20 dev messages and none is wrongly marked in scope; `qwen3:8b`
  takes about 4.6 s per message on an 8 GB laptop GPU.
  ([results/reader/](results/reader/))
- Reader fix: code, not the model, decides whether a message is on the
  corridor; the district is copied from the feed, never guessed; the prompt
  gained five worked examples from real messages.
- First Reader runs on the dev set: `qwen3:4b` flagged 7 of 20; `qwen3:8b`
  parsed all 20 but marked 17 off-corridor messages as in scope.
- Reader runs on local models through Ollama; every call is logged to
  [evidence/ai-log/](evidence/ai-log/).
- 20 real Special Traffic News messages from 15–21 Sep added as the Reader dev
  set ([data/labelled_incidents/](data/labelled_incidents/)).
- Incident Reader (component B): contract schema, validation, retry once then
  flag, 17 tests that need no LLM.
- Python environment: pinned requirements, pytest config.

**Mon 21 Sep**
- Repo created: `CLAUDE.md` and the brief, hackathon, data, architecture, plan
  and pitch docs.

## Quick start

Python 3.11 or newer.

```bash
git clone https://github.com/f1ymango/ripple.git
cd ripple
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest                   # 268 tests, no LLM needed
```

### Run the data layer

```bash
python -m src.loaders.fetch corridor     # writes data/detectors.csv
# incidents come from three STN files (docs/02-data.md §2); fill their cache
# first -- resumable, about 45 min per file for six months
python -m src.loaders.fetch prefetch --feed stn    --start 2026-03-22 --end 2026-09-21
python -m src.loaders.fetch prefetch --feed stn_tc --start 2026-03-22 --end 2026-09-21
python -m src.loaders.fetch prefetch --feed stn_sc --start 2026-03-22 --end 2026-09-21
python -m src.loaders.fetch candidates --start 2026-03-22 --end 2026-09-21
python -m src.loaders.fetch detectors --start 2026-09-21T07:00 --end 2026-09-21T10:00
# the twin's observed data for one replay; --start is the simulation's time 0
python -m src.loaders.fetch twin-detectors --start 2026-05-15T07:55 --end 2026-05-15T10:35
python -m src.loaders.fetch live         # polls the live feeds until stopped
```

Downloads are cached in `data/raw/`, so each machine fills its own cache the
first time. Read [docs/02-data.md](docs/02-data.md) §7 before calibrating on
the detector bins.

### Run the Incident Reader

The model (`qwen3:8b`, run locally through Ollama) only reads what the message
says: road, direction, landmark, lanes closed, incident type. Code copies what
the feed already carries (IDs, text, times, coordinates) and decides whether
the message is about our corridor. Every reply is checked against the
contract, retried once if it fails, then flagged, never used.

Install [Ollama](https://ollama.com), then:

```bash
ollama pull qwen3:8b               # about 4.9 GB, once
python -m src.reader.run           # parses data/labelled_incidents/messages.jsonl
python -m src.reader.run --model qwen3:4b   # same messages, another model
```

Each run writes `results/reader/<time>_<model>.jsonl`. Without a GPU it runs
on the CPU, much more slowly.

To collect real messages from the DATA.GOV.HK archive:

```bash
python -m src.reader.sample --start 2026-09-15 --end 2026-09-21 --n 20 --out dev.jsonl
```

It never overwrites an existing file. Downloads go through the data layer's
cache in `data/raw/` (not committed); run `python -m src.loaders.fetch prefetch
--feed stn ...` first to download a long window in parallel. The gold set
behind the accuracy number is made and labelled as described in
[data/labelled_incidents/LABELLING.md](data/labelled_incidents/LABELLING.md).

### Run the operator console

```bash
streamlit run src/console/app.py
```

![The corridor console at the 21 Sep 08:20 bin: five detectors at or below 30
km/h along the Aberdeen Tunnel approach](docs/img/week1-corridor-map.png)

The map draws all 28 corridor detectors from [data/detectors.csv](data/detectors.csv).
Colour comes from a `data/detector_5min_*.csv` window written by the data
layer; without one, every detector stays grey rather than being given an
invented speed. Pick the window in the sidebar and the bin on the slider —
prefer a full window over a `_cov` export, which is a filtered subset meant for
count calibration ([docs/02-data.md](docs/02-data.md) §7).

## Rules everyone follows

The full list is in [CLAUDE.md](CLAUDE.md). The ones that bite:

- **The LLM never produces a number the simulator can compute.** Every number
  we present comes from `results/`, and nobody edits `results/` by hand.
- **Build to the contracts.** Changing one is a team decision, said out loud
  and written into [docs/03-architecture.md](docs/03-architecture.md) the same day.
- **Never invent data.** If a source is missing, say so. Test stand-ins are
  named `mock_*` and live in `tests/fixtures/`.
- **Log every LLM call** to `evidence/ai-log/`. Prompts live in files under
  `src/*/prompts/`, never inline.
- **Runs are seeded and reproducible.**

## Working in the repo

- One branch per piece of work (e.g. `data/archive-loader`), then a pull
  request to `main`. The Lead merges.
- Add your packages, pinned, under your component's heading in
  [requirements.txt](requirements.txt).
- On Windows, open text files with `encoding="utf-8"`: Python still defaults
  to cp1252 there, and our data is in English and Chinese.

## Docs

| File | What's in it |
|---|---|
| [00-brief.md](docs/00-brief.md) | The product, the components, what is out of scope |
| [01-hackathon.md](docs/01-hackathon.md) | Rules, dates, judging criteria |
| [02-data.md](docs/02-data.md) | Data feeds, schemas and their gotchas |
| [03-architecture.md](docs/03-architecture.md) | JSON contracts between modules |
| [04-plan.md](docs/04-plan.md) | Timeline, roles, critical path |
| [05-pitch.md](docs/05-pitch.md) | Narrative, evidence, Q&A, ethics |

## Data

Traffic detector data and Special Traffic News from
[DATA.GOV.HK](https://data.gov.hk) and the Transport Department. Attribute both
wherever the data is shown. Everything we use is aggregate and open: no
personal data, no vehicle identifiers.
