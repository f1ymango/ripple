# Submission and evidence manifest — updated 18 October 2026

**Media update:** Visuals' [18 October handoff](final-visuals-handoff-2026-10-18.md) adds a [ten-slide review deck](ripple-visual-demo-pitch-2026-10-18-v17-detectors-review.pptx) and [90-second narrated demo](../docs/video/ripple-two-case-website-demo-2026-10-18-v17-detectors-narrated.mp4). The [submission media index](submission/README.md) identifies the current versions and remaining upload gates.

This manifest separates source material from deliverables that have actually
been exported and reviewed. It includes the working
[two-incident source pack](../docs/demo-two-incidents-2026-10-16.md), the
[Lead presentation handoff](../docs/2026-10-15-two-case-demo-handoff.md), and
[Simulation's final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md).
A source draft, passing test or local-only artifact is not a submitted
deliverable. The **16 October results/claims freeze is in effect**. The organiser's
[2026 final-submission instructions](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/)
set the hard deck deadline at **18 October, 23:59 HKT**. The
[Lead delivery checklist](../docs/2026-10-16-freeze-and-delivery-checklist.md)
tracks the mandatory cover fields, file format/name, one-file upload,
prototype links, access checks and post-freeze change rule.

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
| Deck copy | Impact | Draft | [`slides.md`](slides.md), [`qa-sheet.md`](qa-sheet.md), [`costing.md`](costing.md), [`real-vs-simulated.md`](real-vs-simulated.md) | Mark's [15 Oct slide PR #70](https://github.com/f1ymango/ripple/pull/70) is merged as Markdown source, and the two-case claim corrections are on this wrap-up branch. Lead updated the Q&A source for the frozen cut on 16 Oct; Impact must reconcile its open [PR #69](https://github.com/f1ymango/ripple/pull/69) and review the final presenter copy. Impact still needs a two-case consistency pass across slides, Q&A, costing and pitch copy before export. Keep Tuen Mun's modelled-result and queue-limit caption visible. |
| Rendered pitch deck | Visuals + Impact | **Review deck delivered; upload pending** | [Ten-slide PPTX](ripple-visual-demo-pitch-2026-10-18-v17-detectors-review.pptx), [Visuals handoff](final-visuals-handoff-2026-10-18.md) | Slide 5 embeds the narrated demo. Replace role placeholders with verified full names and universities, review captions and playback on the submission machine, then choose the exact one-file upload. No matching PDF export is versioned here. |
| Observed incident prototype | Visuals + Lead | Reviewable code; locally rehearsed | [`../docs/console-observed-playback.md`](../docs/console-observed-playback.md), [`../src/console/app.py`](../src/console/app.py), merged PRs [#53](https://github.com/f1ymango/ripple/pull/53) and [#56](https://github.com/f1ymango/ripple/pull/56) | Show archived TD messages, detector observations, provisional road geometry and the approximate incident callout with their existing labels. It does not establish a route recommendation. |
| Video edit sources | Visuals | Current two-case source delivered | [Narration and route-map source](../docs/video/ripple-two-case-narration-v17.json), [Visuals handoff](final-visuals-handoff-2026-10-18.md), [updated shot list](video-shot-list.md) | The earlier `video-narration.srt` remains historical; use the versioned v17 narration and route-map sources for this cut. |
| Playable two-case video | Visuals | **Delivered; venue playback pending** | [Narrated 90-second MP4](../docs/video/ripple-two-case-website-demo-2026-10-18-v17-detectors-narrated.mp4) | The same MP4 bytes are embedded in slide 5. The frozen modelled-result and queue limitation are narrated. Check playback from a transferred deck before upload. |
| Video source record | Visuals | Reviewable | [Narration JSON](../docs/video/ripple-two-case-narration-v17.json), [Visuals handoff](final-visuals-handoff-2026-10-18.md) | Records the observed detector bin and directed candidate route source; the route map is not live guidance or vehicle replay. |
| Recorded Reader demonstration | Lead + Visuals | Reviewable evidence; pickup not yet captured | Raw messages [`../data/demo_incident_messages.jsonl`](../data/demo_incident_messages.jsonl), saved output [`../results/reader/2026-09-29T1608_qwen3-8b.jsonl`](../results/reader/2026-09-29T1608_qwen3-8b.jsonl), call log [`../evidence/ai-log/2026-09-29.jsonl`](../evidence/ai-log/2026-09-29.jsonl) | Show input beside output for message IDs `138270` and `138272`, labelled “Recorded Qwen3:8b inference — not a live model call.” Retain or flag the first output's known imperfect note. This example is not an accuracy benchmark. |
| Offline recorded B/D capture aid | Lead | Reviewable page; video pickup not yet captured | [Page and rebuild instructions](../evidence/demo/README.md) | Self-contained page displays the saved Reader pair and candidate actions with source hashes and P0 NO-GO. It is not live inference, a rendered video or a recommendation. |
| Reader evaluation | Lead | Reviewable | [`../results/reader/2026-09-25T0048_qwen3-8b_score.json`](../results/reader/2026-09-25T0048_qwen3-8b_score.json), [`../data/labelled_incidents/LABELLING.md`](../data/labelled_incidents/LABELLING.md) | Report initial held-out all-fields-correct scores (50% citywide, 75% corridor) separately from the corrected-prompt development scores (75%, 85%). The 1 October experiment was not adopted. |
| Operator recommendation/approval workflow | Visuals + Lead | Reviewable capability; two saved verdicts | [`../src/console/OPERATOR_WORKFLOW.md`](../src/console/OPERATOR_WORKFLOW.md), [two-case pack](../results/demo-oct16/) | The console can display Aberdeen's no-recommendation verdict and Tuen Mun's model-ranked P2, one incident at a time. Label the Tuen Mun capture as a modelled candidate; it is not live traffic control or an approved public instruction. The Tuen Mun map still depicts Aberdeen, so capture only its comparison panel/result card. |
| Recorded plan generation and capacity rule | Lead | Reviewable candidate plans | [Aberdeen drafts](../data/generated-plans/IN-26-03365-lead-draft-20261013-b/), [Tuen Mun frozen plans](../data/generated-plans/IN-26-02615-lead-capacity-oct15/), [Lead handoff](../docs/2026-10-15-two-case-demo-handoff.md) | D drafted the Tuen Mun actions; a deterministic Lead rule capped P2 from 80% to **11% before fresh-seed runs**. Do not credit the AI with optimising the share or with calculating benefits. |
| Bilingual operator briefing | Lead | Draft; **withheld from public copy as written** | [Tuen Mun single-cell F draft](../data/generated-briefings/IN-26-02615-p2-demo-oct16.json), [Lead review](../docs/2026-10-16-freeze-and-delivery-checklist.md) | Provenance-bound to the packed 50%-compliance, seed-2029 E result. Its −5% token is not the 18-condition −4.3% ranking, and the Chinese text contains the literal drafting instruction `保留正負號`. Preserve the generated artifact; show it publicly only after human-corrected language and operator review. |
| Two-incident P0/P1/P2 comparison | Data + Simulation | Reviewable **modelled** comparison; no measured benefit | [Pack](../results/demo-oct16/), [evidence and result cards](../docs/demo-two-incidents-2026-10-16.md), [Simulation call](../docs/tuen-mun-simulation-final-call-2026-10-15.md) | Aberdeen's P0/P2 tie produces no recommendation. Tuen Mun's frozen 11% P2 ranks before P0 and P1 under the team's rule (−4.3% modelled E delay versus P0, paired 95% interval −5.6% to −3.0% over 18 scored conditions); its queue and recovery mismatch prevents a measured-road-saving claim. |
| Delay, travel-time, CO2 and BCR benefits | Lead + Impact | Measured-road benefits **withheld / unmeasured** | [Simulation call](../docs/tuen-mun-simulation-final-call-2026-10-15.md), [two-case pack](../docs/demo-two-incidents-2026-10-16.md) | A labelled Tuen Mun **modelled delay comparison** may appear in the deck/video. Do not convert it to actual road savings, CO2 savings or BCR; no measured benefit or physically validated replay is approved. |
| User evidence | Impact | Reviewable qualitative note | [`../evidence/interviews/2026-09-26-minibus-driver.md`](../evidence/interviews/2026-09-26-minibus-driver.md) | One anonymous experienced green-minibus driver. Use as qualitative design input, not expert validation, a representative survey or measured performance evidence. Hypothetical figures in the interview stimulus are not Ripple results. |
| Prototype access and final upload | Lead + Impact | **Missing / unconfirmed** | No public prototype link, named uploader or submission receipt is recorded here | Embed prototype/video/technical links in the single uploaded deck, test viewer access, confirm the uploader and preserve the receipt. The organiser locks slides on upload; submit by **18 Oct, 23:59 HKT** after the cover and final number/caption review. |

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

## Freeze-to-submission owner handoff

- **Impact:** review the delivered two-case deck in slideshow mode and check
  each displayed number against the frozen result cards. Keep Aberdeen's
  refusal and Tuen Mun's modelled result and queue limitation clear.
- **Visuals:** the 90-second cut and source record are delivered. Check the
  embedded video and captions from the transferred deck on the actual
  presentation computer; keep the Tuen Mun route labelled as a model candidate.
- **Data and Simulation:** keep the original frozen 11% pack and provenance
  unchanged. The [final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md)
  permits a labelled comparison only. Any correctness fix that changes a run,
  ranking or claim requires a matched rerun and team review before replacement.
- **Lead:** keep the single-cell F draft out of public copy until corrected
  and human-reviewed; check each presented figure and its source, then verify
  deck/prototype access, named uploader and receipt. The organiser's
  [2026 instructions](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/)
  set **18 October, 23:59 HKT** and a locked one-file deck upload. Record the
  exact uploaded file and receipt.
