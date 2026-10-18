# Two-case incident demo — video shot list

> Historical edit notes. The current deliverables are
> `docs/video/ripple-two-case-website-demo-2026-10-18-v17-detectors-narrated.mp4`
> and `deck/ripple-visual-demo-pitch-2026-10-18-v17-detectors-review.pptx`.
> Earlier rough-cut exports named below were removed before the final push.

## Current speech-led website demo — 15 October

The current 90-second review export is
`docs/video/ripple-two-case-website-demo-2026-10-16-v9.mp4`. It replaces the
motion/slideshow cut for the live pitch: actual 1920 × 1080 console footage
fills the frame, the Aberdeen incident marker remains stable while detector
bins change, and Tuen Mun's real comparison is highlighted P0 → P1 → P2. The
edit is intentionally silent for the team's live speech; use
`deck/website-demo-presenter-cues-2026-10-15.md`. It shows one Tuen Mun
simulation condition and a saved F draft pending human review. The Tuen Mun
footer carries Simulation's short queue/recovery caveat from its final 15 Oct
call. The v5 timing
table below describes the earlier motion review, not this website demo.

| Time | Actual website demonstration |
| --- | --- |
| 0–37 s | Aberdeen observed map and changing five-minute readings; editorial footer notes the tested-plan tie. |
| 37–48 s | Original TD incident notice and speed chart. |
| 48–75 s | Tuen Mun single-condition P0/P1/P2 comparison, with editorial focus outlines. |
| 75–90 s | Saved briefing draft and operator decision controls; no approval is recorded. |

## Current Visuals edit — 15 October, for Lead/Impact review

The 14 October Aberdeen-only cut and its narration are superseded by the
[Lead's two-case handoff](../docs/2026-10-15-two-case-demo-handoff.md). The
working cut gives Aberdeen and Tuen Mun roughly equal time within the incident
story. It uses Data's frozen two-case pack at `c4ec872`. This is a **review
draft** until the 16 October P0/ranking check and Lead's public wording lock.
The final submission deck must stand on its own when a video or external link
cannot play on the organiser's preloaded computer.

The organiser's submission instructions supplied on 15 October require **one
deck file** in `.ppt`, `.pptx` or `.pdf` by **18 October, 23:59 HKT**. Slides
lock at upload, cannot be revised or presented from our own laptop, and the
pitch is limited to five minutes. The first slide needs team name, project
title, track, a description of at most 30 words, and every member's full name
and university; the filename must be `Team Number – [Team Name]`. The deck
must be primarily English. Prototype proof belongs inside the deck: embed
the reviewed video or include a tested access link, while keeping still proof
of the working console and comparison readable offline. Impact owns the final
deck assembly and the uploader/access check.

| Time | Visual and claim | Source boundary |
| --- | --- | --- |
| 0–16 s | Animated operator problem and four-step Ripple workflow. | Product framing; no measured improvement claim. |
| 16–24 s | **Aberdeen.** Archived 15 May TD notice names Wong Chuk Hang Road flyover. | Report publication and approximate site, not a physical closure-time measurement. |
| 24–33 s | Real console recording: five-minute detector map and readings change. | TD observations; no route recommendation or evaluated vehicle tracks. |
| 33–39 s | Saved bilingual Reader input/output beside its source. | Recorded Qwen3:8b inference, not a live call or accuracy benchmark. |
| 39–48 s | **No clear winner.** Ripple withholds a plan recommendation. | `results/demo-oct16/aberdeen/verdict.json`; no claim that every real intervention fails. |
| 48–55 s | **Tuen Mun.** Illustrated road schematic closes two lanes in sequence. | TD reported only one lane available; illustration is not a vehicle replay. |
| 55–64 s | P0/P1/P2 response cards and advice-share bars build in sequence. | P0 no added advice; P1 fixed blanket comparator; P2 capacity-bounded 11% candidate. |
| 64–73 s | Animated 18-condition result: P0 0%, P1 +37.3%, P2 −4.3%. | **Prototype simulation, 18 scored conditions.** Mean paired E-delay differences versus P0, not observed road savings; P0 queue/recovery limitation stated. |
| 73–80 s | Actual Tuen Mun console comparison capture with a slow focus move. | One displayed 50%-compliance, seed-2029 condition; not the 18-condition mean. |
| 80–90 s | One operator workflow, two outcomes; human review before public advice. | F's bilingual Tuen Mun text is still a draft. Do not film it as approved VMS/public copy. |

Editable scene source: `docs/video/judge-cut-motion-2026-10-15.html`.
The Tuen Mun console crop is `docs/img/tuen-mun-console-comparison-2026-10-15.png`.
The 90-second motion review is
`docs/video/ripple-two-case-90s-motion-review-2026-10-15-v5.mp4`, with an
adjacent source-hash manifest. It embeds a cropped excerpt of the archived
Aberdeen console recording and an actual Tuen Mun comparison-panel capture.
It remains silent until a continuous human voice track is recorded and checked.

## Judge-first review recut — 15 October

The earlier v3 review depended too much on knowing the project already. The
captioned v4 review was
`docs/video/ripple-two-case-90s-judge-review-2026-10-15-v4.mp4`, rendered from
`docs/video/judge-cut-scenes-2026-10-15.html`. Its large on-screen sentences
make the story understandable without audio. The matching connected human
recording script is `deck/video-voiceover-judges-2026-10-15.md`.

| Time | What an outsider sees |
| --- | --- |
| 0–16 s | The operator's crash-response problem, then Ripple's four-step workflow: read, draft, simulate, human decide. |
| 16–48 s | Aberdeen's archived flyover crash, observed detector playback, saved AI Reader, then the no-recommendation outcome. |
| 48–80 s | A clearly labelled Tuen Mun closure schematic, P0/P1/P2 advice choices, the 18-condition model result, then a real console comparison capture. |
| 80–90 s | Two outcomes side by side; an operator decides before advice is sent. |

The Tuen Mun lane drawing illustrates the archived TD report that only one lane
remained. It is not an evaluated vehicle trajectory or a route map. The
−4.3%/ +37.3% chart is an 18-condition model comparison, while the console
capture shows one matched condition. The current v5 motion review retains those
labels and adds real Aberdeen playback, sequenced lane and plan animations,
moving result bars, and a guided focus move over the Tuen Mun console capture.
It remains a local silent review until a coherent human narration is recorded,
synchronized, and tested in the submission deck.
Two slide inserts for Impact: `deck/two-case-visuals-review-2026-10-15.html`
and its review PDF. The video MP4 stays local, as previously agreed; the source
script and evidence labels can be reviewed in Git.

For a final cut, replace the silent timing review with **one human narration**
using `deck/video-voiceover-judges-2026-10-15.md`, then time the captions to that
recording. Check the final file from the submitted slide file on a separate
computer or account. If the 16 October matched P0 or ranking changes, update
the chart, narration, slides and source manifest together before upload.

## Historical Aberdeen-only edit — 14 October

Owner: Visuals. Updated 12 October against the existing 92.6-second silent rough
cut. This follows the approved [9 October observed-playback scope](../docs/04-plan.md).
The recording is local, separate from Git. This table describes the shots
already captured; the required Reader pickup below is not yet integrated.

## Current cut

| Video time (approx.) | Screen | Evidence and narration purpose |
| --- | --- | --- |
| 0–5.45 s | Ripple title | Introduce an incident co-pilot for traffic operators. |
| 5.45–17.46 s | May 15, 09:05 HKT; small incident arrow | Archived TD 09:01 partial-lane report in `data/demo_incident_messages.jsonl`. Position is approximate, derived from the named flyover and landmark geometry. |
| 17.46–29.46 s | Rewind to 08:50; corridor road graph | Earlier detector observations. No report is yet published at this cursor. Road curves are context, not recommended routes. |
| 29.46–45.47 s | 09:15 detector map | Recorded observations in the full May five-minute export. AID01103/01104/01106 have 40% archive coverage at this bin; do not infer continuous monitoring or a detour share. |
| 45.47–59.47 s | 09:40; updated callout | The archived 09:36 TD message reports all lanes closed. Its publication time is distinct from an inferred physical closure time. |
| 59.47–71.48 s | 10:25; clearance state | The loader's incident CSV records the 10:02 clearance report. AID01103/01104/01106 have 20% coverage in the displayed later bin. |
| 71.48–92.60 s | Comparison/approval waiting state, then closing card | Comparable evaluated plans are unavailable. No recommended route, evaluated vehicle animation or benefit claim is presented. |

The full export is `data/detector_5min_20260515-0755_1035_b5.csv`, not the
filtered `_cov40` calibration file. Source and setup details are in
[the playback guide](../docs/console-observed-playback.md). The local video's
adjacent source manifest records capture input hashes; those hashes do not
establish evaluated-run provenance.

[Draft timed narration](video-narration.srt) matches this cut. It is an editing
and recording script, not a transcript of an existing audio track: the rough
cut is silent. Re-time it after Rorath records the voice track and reviews pacing.

## Required GenAI evidence pickup — not yet captured

The current cut shows archived TD prose, detector observations and the waiting
state; none of those screens visibly demonstrates model inference. Add a short
input/output shot using the already saved Reader evidence:

- Put the raw archived message beside its corresponding parsed JSON for message
  IDs `138270` and `138272`.
- Capture aid: the [offline recorded B/D page](../evidence/demo/README.md),
  which shows the selected source and output together and keeps its status
  banner visible. The underlying input is `data/demo_incident_messages.jsonl`,
  output is `results/reader/2026-09-29T1608_qwen3-8b.jsonl`, and call record is
  `evidence/ai-log/2026-09-29.jsonl`.
- On-screen label: **Recorded Qwen3:8b inference — not a live model call.**
- Show the useful change from `lanes_closed: ["unspecified"]` in the first
  report to `["all"]` in the later update. Keep source prose and model output
  visually distinct.
- Do not silently edit the first saved output's free-text note, which
  overdescribes the direction bracket. Retain it or add a visible limitation.
- A selected two-message example is not an accuracy benchmark. If scores are
  shown, distinguish initial held-out 50%/75% from corrected-prompt development
  75%/85%; the 1 October experiment was not adopted.

Re-time the cut and `video-narration.srt` only after the edited media is
available for review. No new Ollama call is needed for this pickup.

## Optional GenAI capability pickup — review before capture

For the separate GenAI capability pickup, use the same
[offline recorded B/D page](../evidence/demo/README.md) and the
[13 October Lead handoff](../docs/lead-genai-handoff-2026-10-13.md): they identify
the real generated D artifacts and limitations. Show the inputs and candidate
actions, labelled **Recorded GenAI draft — retrospective working assumptions;
not evaluated**. Do not turn this into the plan-comparison shot below. Capture
and integration remain pending; the current-cut timestamps above are unchanged.
F's later 13 October synthetic retries passed structural validation but failed
[semantic review](../docs/lead-genai-follow-up-2026-10-13.md). Do not add a
successful F-generation shot from those calls. Existing fixture UI may be
shown only as tested synthetic capability, not a new generated briefing.

## Optional later shots — require accepted simulation evidence

- **SUMO:** `results/twin/aberdeen-diagnostic.gif` belongs to the September
  IN-26-06481 diagnostic, not the May pre-incident window. Omit it from this
  May observed-playback cut. If separately approved as a technical excerpt,
  label it “Earlier September diagnostic — not the May incident; unvalidated.”
- **Plan comparison:** include only after Lead, Data and Simulation accept
  one matching run bundle. A calendar date or passing CI does not open this gate.

## Final edit checks

- Retain the archived date, HKT, coverage, approximate-position qualifier and
  TD/DATA.GOV.HK plus OpenStreetMap/CARTO attribution.
- Do not use detector-inferred lane phases as raw TD messages. In particular,
  `results/data/closed-lanes_AID01104_20260515-0840_1010.json` is an inference
  artifact, not an incident-message log.
- Keep delay, CO2, travel-time savings and BCR unclaimed unless supported by
  accepted comparable runs before the provisional 16 October results freeze.
- Deliver the next reviewable evidence/export pack on 15 October; review the
  final delta on the 16th and target internal submission on 17 October ahead
  of the 18 October deadline. Follow `docs/04-plan.md`.
- Check narration, subtitle timing, map readability and the delivery format
  on the submission platform before final delivery.
