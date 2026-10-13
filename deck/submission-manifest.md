# Submission and evidence manifest — 13 October 2026

This manifest separates source material from deliverables that have actually
been exported and reviewed. This update is based on main commit
`8a62382341464ea067ad344699b364f48496364d` plus the linked 13 October GenAI
deliverables. A source draft, passing test or
local-only artifact is not a submitted deliverable.

Status terms:

- **Reviewable** — versioned source exists and its stated evidence boundary has
  been reviewed.
- **Draft** — usable source exists, but final editorial or media review remains.
- **Missing** — the repository does not contain the expected deliverable.
- **Withheld** — an artifact exists as a diagnostic, but current evidence does
  not permit the associated public claim.

## Delivery inventory

| Item | Owner | Status | Source or delivery path | Allowed use and remaining acceptance |
| --- | --- | --- | --- | --- |
| Deck copy | Impact | Draft | [`slides.md`](slides.md), [`qa-sheet.md`](qa-sheet.md), [`costing.md`](costing.md), [`real-vs-simulated.md`](real-vs-simulated.md) | Source copy for all five judging criteria. Final editorial and visual review remains. Unsupported benefit and operating-cost figures stay omitted. |
| Rendered pitch deck | Impact | **Missing** | No `.pptx` or presentation `.pdf` in `deck/` at this checkpoint | Supply an editable source and reviewable export; verify fonts, links, citations and slide readability before delivery. `docs/img/interim-console-2026-10-02.pdf` is a historical console image, not the deck. |
| Observed incident prototype | Visuals + Lead | Reviewable code; locally rehearsed | [`../docs/console-observed-playback.md`](../docs/console-observed-playback.md), [`../src/console/app.py`](../src/console/app.py), merged PRs [#53](https://github.com/f1ymango/ripple/pull/53) and [#56](https://github.com/f1ymango/ripple/pull/56) | Show archived TD messages, detector observations, provisional road geometry and the approximate incident callout with their existing labels. It does not establish a route recommendation. |
| Video edit sources | Visuals | Draft | [`video-shot-list.md`](video-shot-list.md), [`video-narration.srt`](video-narration.srt) | The shot list describes a 92.6-second silent rough cut held outside this repository. The narration is a draft, not an existing audio track. |
| Playable rough cut / final video | Visuals | **Missing** | No `.mp4`, `.mov` or `.webm` in the inspected workspace | Supply an accessible review artifact, then check pacing, map legibility, coverage labels, narration, captions and attribution. |
| Video source manifest | Visuals | **Missing** | Described as adjacent to Visuals' local rough cut; no file or verified link is recorded here | Supply the manifest with the cut. Capture hashes establish which display inputs were used, not evaluated-run provenance. |
| Recorded Reader demonstration | Lead + Visuals | Reviewable evidence; pickup not yet captured | Raw messages [`../data/demo_incident_messages.jsonl`](../data/demo_incident_messages.jsonl), saved output [`../results/reader/2026-09-29T1608_qwen3-8b.jsonl`](../results/reader/2026-09-29T1608_qwen3-8b.jsonl), call log [`../evidence/ai-log/2026-09-29.jsonl`](../evidence/ai-log/2026-09-29.jsonl) | Show input beside output for message IDs `138270` and `138272`, labelled “Recorded Qwen3:8b inference — not a live model call.” Retain or flag the first output's known imperfect note. This example is not an accuracy benchmark. |
| Reader evaluation | Lead | Reviewable | [`../results/reader/2026-09-25T0048_qwen3-8b_score.json`](../results/reader/2026-09-25T0048_qwen3-8b_score.json), [`../data/labelled_incidents/LABELLING.md`](../data/labelled_incidents/LABELLING.md) | Report initial held-out all-fields-correct scores (50% citywide, 75% corridor) separately from the corrected-prompt development scores (75%, 85%). The 1 October experiment was not adopted. |
| Operator recommendation/approval workflow | Visuals + Lead | Reviewable capability with fixtures | [`../src/console/OPERATOR_WORKFLOW.md`](../src/console/OPERATOR_WORKFLOW.md), `tests/fixtures/mock_recommendation/` | May demonstrate provenance checks, briefing display and audit actions only when visibly labelled as fixture data. It is not a real recommendation for IN-26-03365. |
| Real-model plan generation | Lead | Draft; constraints and evaluator action mapping checked | [`../data/generated-plans/IN-26-03365-lead-draft-20261013-b/`](../data/generated-plans/IN-26-03365-lead-draft-20261013-b/), [review and hashes](../docs/lead-genai-handoff-2026-10-13.md) | Recorded Qwen3:8b output using retrospective working assumptions. Not evaluated or approved. Retain the P1 title limitation and assumed P2 signal control; capture remains pending. |
| Real-model bilingual briefing | Lead | **Missing accepted output**; failed attempts logged | [F outcome and fixture helper](../docs/lead-genai-handoff-2026-10-13.md), [`../evidence/ai-log/2026-10-13.jsonl`](../evidence/ai-log/2026-10-13.jsonl) | Initial request timed out; bounded retry failed validation. Do not show rejected text as a finished briefing or imply the existing synthetic UI was generated by these calls. Human bilingual review remains pending. |
| Incident P0 and rehearsal P1/P2 | Data + Simulation | **Withheld** from public comparison | PR [#61](https://github.com/f1ymango/ripple/pull/61), [joint review](../docs/evaluator-p0-go-no-go-2026-10-09.md) | Evaluator and software guardrails are merged. Scientific NO-GO remains: rehearsal plans are not the new model-generated set and no accepted comparable incident bundle exists. |
| Delay, travel-time, CO2 and BCR benefits | Lead + Impact | **Withheld / unmeasured** | No accepted comparable incident result set | Omit unless every acceptance gate in [`../docs/04-plan.md`](../docs/04-plan.md) is met before the provisional 16 October freeze (hour unconfirmed). The extension does not imply acceptance. |
| User evidence | Impact | Reviewable qualitative note | [`../evidence/interviews/2026-09-26-minibus-driver.md`](../evidence/interviews/2026-09-26-minibus-driver.md) | One anonymous experienced green-minibus driver. Use as qualitative design input, not expert validation, a representative survey or measured performance evidence. Hypothetical figures in the interview stimulus are not Ripple results. |
| Prototype access and final upload | Lead + Impact | **Missing / unconfirmed** | No public prototype link, named uploader or submission receipt is recorded here | Confirm the delivery format, sharing permissions, uploader and upload receipt before the 17 October internal target. |

## Local replay inputs on the Lead laptop

These files were present on 12 October and supported the 11 October rehearsal.
They are ignored/local inputs, not versioned submission deliverables:

| Local path | Use and limitation |
| --- | --- |
| `data/detector_5min_20260515-0755_1035_b5.csv` | Full five-minute export for observed playback. Do not substitute the filtered `_cov40` calibration subset. |
| `data/incidents_2026-05-15_2026-05-15.csv` | Incident timeline containing IN-26-03365's report and clearance. |
| `sim/work/lead-demo-oct11/aberdeen.net.xml` | Optional provisional road geometry. SHA-256 `e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e`; not an accepted network release or route proof. |

Rebuild and rehearsal instructions, archive coverage and checked timestamps are
in the [observed-playback guide](../docs/console-observed-playback.md). Do not
refetch these inputs solely to recreate an unchanged check.

## Consolidated owner handoff — draft, not sent

- **Impact:** provide a reviewable deck export and editable source; map each
  public claim to this evidence pack; cover all five judging criteria; retain
  blank/unmeasured benefits and costs where evidence is absent.
- **Visuals:** provide an accessible rough or final cut, captions and its source
  manifest; add the recorded-Reader pickup and review the separately labelled
  D/F material in the [GenAI handoff](../docs/lead-genai-handoff-2026-10-13.md); state
  explicitly if final delivery is not yet available.
- **Data and Simulation:** preserve the joint incident-P0 limitations and state
  explicitly if no additional accepted run bundle will arrive before freeze.
  Diagnostic artifacts must remain separate from public benefit claims.
- **Lead and Impact:** confirm the final uploader, prototype/deck/video access,
  platform format requirements and receipt. Deliver the usable pack on
  15 October, review a final delta by the provisional 16 October freeze, and
  target internal submission on 17 October. No cutoff hour is agreed, and no
  additional simulation acceptance is promised.
