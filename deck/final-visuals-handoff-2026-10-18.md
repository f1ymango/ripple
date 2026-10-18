# Visuals handoff — 18 Oct 2026

The pitch deck must be submitted by **23:59 HKT today** as one PPTX or PDF. The submitted file is locked for the 24 Oct pitch. The live presentation has a five-minute limit.

## Reviewable artifacts

- Current local submission review deck: `deck/ripple-visual-demo-pitch-2026-10-18-v17-detectors-review.pptx` (ten slides). Slides 1–7 are in live-pitch order; slide 5 embeds the voiced 90-second video and is set to start automatically. Slides 8–10 are case-study backup. This retains the 17 Oct deck's result content and adds the Tuen Mun detectors and route-map insert to the video. The original in Downloads is untouched. The route version still needs a final slideshow play check on the submission machine.
- Current narrated 90-second demo: `docs/video/ripple-two-case-website-demo-2026-10-18-v17-detectors-narrated.mp4`; narration text and source explanation: `docs/video/ripple-two-case-narration-v17.json`. From 50–59 seconds the map shows all 27 TD roadside detectors, coloured by their observed 18:00 HKT speed, and traces the frozen P2 Castle Peak Road detour in magenta from its 34 ordered SUMO edges. Larger white dots mark junctions; the crash marker is separate. The working console's plan comparison follows. The network, selected run scenario, and detector observations SHA-256 values match the saved P2 run provenance. The map is a simulated route candidate over observed detector readings, not live advice or a vehicle replay.
- The console also now displays that provenance-bound Tuen Mun path, the 27 detectors with a selectable five-minute observed bin, and the selected junction nodes below the Tuen Mun comparison. This path was visually checked in a local browser against the detailed map, and the 90-second MP4 fully decoded. The embedded MP4 bytes match the standalone export, and the PPTX has no external media links. Superseded local deck and video exports were removed before preparing the push.

## Evidence-safe story

1. Ripple reads an archived TD incident notice, structures its content, proposes constrained response options, compares them in seeded SUMO runs, and leaves the action to an operator. The LLM does not compute traffic metrics.
2. Aberdeen: archived TD notices and detector bins play on the map. In the frozen saved comparison, no tested plan clearly beats P0; P2 ties under the team ranking rule, so the console withholds a route recommendation. The saved result is diagnostic: five referenced original simulation inputs are absent from merged main, so do not claim that Aberdeen is fully reproducible from the repository.
3. Tuen Mun: archived detector speeds show the incident; in the frozen simulation, targeted 11% P2 averages 4.3% less total delay than P0 across 18 conditions, with lower modelled delay in 17 of 18. Broad P1 averages 37.3% more. The queue moves too fast, clears early, and releases too much traffic after reopening. These are modelled comparisons, not measured road savings or operational advice.

## Five-minute pitch path

Run slides 1–7 in order: 0:00–1:50 for slides 1–4, 1:50–3:20 for the automatically playing slide 5 video, and 3:20–4:20 for slides 6–7. Slides 8–10 are backup for questions. The video now speaks for itself, so avoid talking over its narration. Use `five-minute-pitch-cues-2026-10-18.md` for the full timed script.

## Before upload

- Submission owner: replace slide 1 role placeholders with every member's **full name and university**; confirm the registered team name/number and filename `Team Number – [Team Name].pptx`. The current local files do not establish the complete roster.
- Submission owner: copy the preferred deck to a second machine and play slide 5 from the transferred PPTX. The local PowerPoint preview passed, but the organizer's playback setup is still unverified. The case-study slides provide a live-pitch fallback.
- Submission owner: rehearse slides 1–7, inspect the whole deck in slideshow mode, verify animations/video, and upload a single final file before 23:59 HKT. Keep the upload receipt.

Frozen results and claims should only change after the team flags a critical correctness issue. No frozen result files were changed for this handoff.
