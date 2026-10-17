# Visuals handoff — 18 Oct 2026

The pitch deck must be submitted by **23:59 HKT today** as one PPTX or PDF. The submitted file is locked for the 24 Oct pitch. The live presentation has a five-minute limit.

## Reviewable artifacts

- Preferred submission review deck: `deck/ripple-visual-demo-pitch-2026-10-18-v11-appendix-review.pptx` (ten slides, including an embedded video appendix). This is a copy of the 17 Oct deck; the original in Downloads is untouched. Slide 7 now labels the `17 / 18` result as lower **modelled** delay, and slide 5 notes record the Aberdeen provenance limitation. It opens in PowerPoint; slide 7 was visually checked, and the embedded video played in PowerPoint slideshow mode on this Mac.
- The 90-second v11 demo is embedded in the PPTX. Its source hash and verification are recorded in `docs/video/ripple-two-case-website-demo-2026-10-18-v11.sources.json`, with live narration in `deck/website-demo-presenter-cues-v10-2026-10-18.md`. The standalone MP4 remains a local Visuals export and is intentionally not committed to this review branch. It has explanatory captions for silent viewing and remains silent for live narration. The older v9 exposes an unreviewed operator briefing draft and must not be used.
- The deck's Aberdeen and Tuen Mun GIF slides already show recorded prototype/observed playback. Slide 10 contains the embedded v11 video. The deck has no local MP4 link to break when transferred.

## Evidence-safe story

1. Ripple reads an archived TD incident notice, structures its content, proposes constrained response options, compares them in seeded SUMO runs, and leaves the action to an operator. The LLM does not compute traffic metrics.
2. Aberdeen: archived TD notices and detector bins play on the map. In the frozen saved comparison, no tested plan clearly beats P0; P2 ties under the team ranking rule, so the console withholds a route recommendation. The saved result is diagnostic: five referenced original simulation inputs are absent from merged main, so do not claim that Aberdeen is fully reproducible from the repository.
3. Tuen Mun: archived detector speeds show the incident; in the frozen simulation, targeted 11% P2 averages 4.3% less total delay than P0 across 18 conditions, with lower modelled delay in 17 of 18. Broad P1 averages 37.3% more. The queue moves too fast, clears early, and releases too much traffic after reopening. These are modelled comparisons, not measured road savings or operational advice.

## Five-minute pitch path

Use slides 1–4 for the problem and working AI Reader, then present slides 5–7 with their GIFs and chart, and finish with slides 8–9. Slide 10 is optional prototype proof for independent review. If the team elects to play the video live, skip the full slide 5–7 explanation: allow 0:00–1:50 for slides 1–4, 1:50–3:20 for the video, and 3:20–4:20 for slides 8–9, leaving 40 seconds for transitions. Rehearse the jump to and from appendix slide 10 on the presentation computer. The video can be narrated with `website-demo-presenter-cues-v10-2026-10-18.md`.

## Before upload

- Impact/Lead: replace slide 1 role placeholders with every member's **full name and university**; confirm the registered team name/number and filename `Team Number – [Team Name].pptx`. The current local files do not establish the complete roster.
- Visuals/Impact: copy the preferred deck to a second machine and play slide 10 from the transferred PPTX. The local PowerPoint test passed, but the organizer's playback setup is still unverified. The existing GIFs and chart provide a live-pitch fallback.
- Lead/Impact: rehearse the five-minute sequence, inspect the whole deck in slideshow mode, verify animations/video, and upload a single final file before 23:59 HKT. Keep the upload receipt.

Frozen results and claims should only change after the team flags a critical correctness issue. No frozen result files were changed for this handoff.
