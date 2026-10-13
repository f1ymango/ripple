# Observed incident demo — video shot list

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
- Input: `data/demo_incident_messages.jsonl`.
- Output: `results/reader/2026-09-29T1608_qwen3-8b.jsonl`.
- Call record: `evidence/ai-log/2026-09-29.jsonl`.
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

For the separate GenAI capability pickup, use the
[13 October Lead handoff](../docs/lead-genai-handoff-2026-10-13.md): it identifies
the real generated D artifacts and limitations. Show the inputs and candidate
actions, labelled **Recorded GenAI draft — retrospective working assumptions;
not evaluated**. Do not turn this into the plan-comparison shot below. Capture
and integration remain pending; the current-cut timestamps above are unchanged.
F's 13 October real-model fixture attempts failed validation. Do not add a
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
