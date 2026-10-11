# Observed incident demo — video shot list

Owner: Visuals. Updated 8 October against the existing 92.6-second silent rough
cut. This is the observed-playback scope approved in the Lead's reply relayed
by Rorath; final scope remains subject to the 9 October decision. The recording
is local, separate from Git. This table replaces the earlier proposed sequence
with the shots actually captured.

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

## Optional later shots — require a scope decision

- **Reader:** show a saved model output beside its actual input, labelled as
  recorded inference. The current map card displays archived TD prose; it is
  not a new Reader execution. If quoting Reader accuracy, retain the held-out
  versus development distinction and the correct artifact described in
  [the evidence review notes](video-evidence-review.md).
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
  accepted comparable runs before the 14 October results freeze.
- Prepare the reviewable draft for 12 October; target internal submission on
  17 October ahead of the 18 October deadline. Follow `docs/04-plan.md`.
- Check narration, subtitle timing, map readability and the delivery format
  on the submission platform after the final scope decision.
