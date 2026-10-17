# Website demonstration — live presenter cues (v10, 90 seconds)

Play `docs/video/ripple-two-case-website-demo-2026-10-18-v10.mp4` silently and speak over it. This edit shows recorded prototype behaviour; it is not a live traffic feed. The Tuen Mun lane diagram is illustrative, while the comparison panel is a capture of the working console.

| Video time | On screen | Suggested line |
| --- | --- | --- |
| 0–37 s | Aberdeen map advances through archived five-minute detector readings. | “Ripple helps traffic operators decide whether to advise a detour. This map replays archived Aberdeen traffic readings. Each dot is a detector, not a simulated car. As the five-minute readings change, the operator can see where traffic slowed. In the saved plan comparison, no tested plan clearly beats doing nothing, so Ripple holds back.” |
| 37–48 s | Original TD incident notice and observed speed chart. | “The original Transport Department notice stays beside the speed chart. The operator can inspect what was reported and what the detectors recorded.” |
| 48–50 s | Tuen Mun crash and one-open-lane schematic. | “Here is a second incident in Tuen Mun.” |
| 50–75 s | Real console compares no new advice (P0), blanket detour (P1), and limited targeted advice (P2). | “Now the console tests three responses: no new advice, a blanket detour, and targeted advice for a limited share of drivers. These cards show one matched simulation condition. Across 18 tested conditions, targeted P2 averaged 4.3 percent less **modelled** delay than P0. The simulated queue moved too fast, cleared early, and released too much traffic after reopening. This is a candidate for further validation, not a measured road saving.” |
| 75–90 s | Console proof and two-case closing card. | “The two outcomes matter: withhold advice when tests tie, or show an operator a promising modelled candidate. A human makes the final decision before any advice is sent.” |

The Aberdeen result is a saved diagnostic. Its provenance sidecars hash inputs, but five original simulation inputs are absent from merged main, so do not describe the Aberdeen pack as fully reproducible from the repository. The Tuen Mun 4.3% is the frozen 18-condition mean; the console cards show one 50%-compliance, seed-2029 condition. No operator approval or road saving is shown. Do not use the older v9 cut: it displays an unreviewed F briefing draft.
