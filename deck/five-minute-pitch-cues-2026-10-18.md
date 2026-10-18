# Five-minute pitch cues — presentation-order deck

Use `ripple-visual-demo-pitch-2026-10-18-v17-detectors-review.pptx`. Slides 1–7 form the live pitch in order; slides 8–10 are case-study backup. The narrated, captioned video starts automatically on slide 5; let its audio play without speaking over it. Aim to finish by **4:20**, leaving 40 seconds for playback or transition delays.

| Clock | Slide | Suggested words and action |
| --- | --- | --- |
| 0:00–0:25 | 1 — Ripple | “A road closure can shift congestion onto the next road. Traffic operators need to decide whether a detour will help the whole corridor. Ripple helps them test that decision before advice goes out.” |
| 0:25–0:48 | 2 — Corridor | “A blocked link is only the beginning. Drivers move, queues move, and a quick detour can make another route worse. We compare responses at corridor level, rather than treating the incident point alone.” |
| 0:48–1:25 | 3 — Workflow | “The Reader structures a Transport Department notice. A second AI stage proposes constrained options. Seeded SUMO runs calculate the traffic metrics; the language model does not. The console presents the evidence and leaves the decision with a human operator.” |
| 1:25–1:50 | 4 — Reader | “Here is the working Reader on an archived Aberdeen notice. The source says only ‘part of the lanes,’ so Ripple preserves the lane count as unspecified. It does not invent a closure detail.” |
| 1:50–3:20 | 5 — 90-second demo | Advance to slide 5; the embedded video starts automatically and explains both cases. Stay silent while it plays. |
| 3:20–3:50 | 6 — Pilot | “The next step is one supervised corridor pilot: run alongside current practice, compare proposed advice with observed outcomes, and let operators review every action. The simulated Tuen Mun result is promising, but its queue clears too early, so it is not a measured road saving.” |
| 3:50–4:20 | 7 — Close | “Ripple already demonstrates two useful outcomes: hold advice when tested options tie, and show a modelled candidate when one ranks ahead. We are asking for a corridor to validate this with operators before deployment.” |

The video narration covers Aberdeen's observed detectors and saved refusal, then Tuen Mun's 27 observed detector locations, simulated P2 path, and modelled comparison. If the video audio fails on the venue computer, describe these points aloud and emphasize the queue limitation. The full voiceover is in `../docs/video/ripple-two-case-narration-v17.json`.

Slides 8–10 are backup: Aberdeen verdict, Tuen Mun observed playback, and the Tuen Mun modelled comparison. Do not advance into them after the closing slide unless asked. Keep the Aberdeen result described as a saved diagnostic; five referenced original simulation inputs are absent from merged main. The video is a recording of the prototype, not a live traffic feed. No recommendation has been issued to road users.
