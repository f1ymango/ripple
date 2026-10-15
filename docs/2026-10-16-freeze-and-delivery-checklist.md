# 16 October claim freeze and final delivery — Lead checklist

**Decision:** freeze the saved two-incident comparison on 16 October HKT. The
internal submission target is 17 October; the organiser's [2026 deliverables
page](https://www.hack4sdg.com/deliverables/) confirms an 18 October deadline.
The exact upload hour, format and form rules still need a live-form check.

## Locked source set

- [x] Aberdeen: the [saved verdict and provenance](../results/demo-oct16/aberdeen/)
  show a P0/P2 tie and no recommendation.
- [x] Tuen Mun: the [frozen 11% plan, matched results, ranking and provenance](../results/demo-oct16/tuen-mun/)
  put P2 before P0 and P1 under the team's ranking rule. The −4.3% figure is
  **modelled E delay across 18 scored conditions**, not measured road saving.
- [x] Simulation's [final call](tuen-mun-simulation-final-call-2026-10-15.md)
  permits a labelled modelled-candidate comparison, not a measured benefit.
  Its short on-screen caption is in the [two-case evidence pack](demo-two-incidents-2026-10-16.md).
- [ ] Integrate the frozen pack and final-call source into `main` after the
  normal review/CI checks, without substituting diagnostic runs.

## Deliverable gates before the 17 October internal target

| Owner | Check | Status at 15 Oct |
| --- | --- | --- |
| Lead + Impact | Every displayed number and caption points to the [source manifest](../deck/submission-manifest.md) and the observed/modelled distinction is visible. | Pending final export review |
| Lead | Human bilingual/operator review of the [single-cell F draft](../data/generated-briefings/IN-26-02615-p2-demo-oct16.json) if it appears publicly. Do not present it as an approved sign or use its about −5% token as the grid result. | Pending |
| Impact | Export an editable deck and reviewable pitch file covering both cases and the five judging criteria; check visual readability, captions and citations. | No rendered deck in the repository at this checkpoint |
| Visuals | Deliver a balanced playable two-case cut with captions and a source manifest. Show Tuen Mun's comparison panel/result card, not the Aberdeen map. | No playable final video in the repository at this checkpoint |
| Lead + uploader | Inspect the live 2026 form for exact upload requirements; test prototype/deck/video access from a viewer account; record who submits and preserve the receipt. | Pending |

## Post-freeze change rule

After the claim freeze, continue deck/video editing, accessibility and link
checks, reproducibility checks, and ordinary bug fixes that leave the frozen
inputs, rankings and public claims unchanged. A correctness issue that changes
a scenario, plan, result, ranking, captioned number or verdict is **not** a
silent polish fix: preserve the old artifact, rerun the affected comparison
on matched inputs, obtain Data/Simulation/Lead review and update every dependent
slide/video/briefing statement before replacing it. If that cannot be done in
time, retain the existing qualified story or remove the affected claim.

The presentation balance, wording and asset handoff live in the
[Lead two-case handoff](2026-10-15-two-case-demo-handoff.md); this checklist
records delivery gates, not a second source of result figures.
