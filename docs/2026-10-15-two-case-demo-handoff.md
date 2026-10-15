# Two-case demo handoff — Lead, 15 October 2026

**Direction:** Keep Visuals' existing 92.6-second Aberdeen rough cut as the
editable base. Add a removable **15–25-second Tuen Mun insert** after Aberdeen's
plan verdict. Visuals owns final pacing; the project target is approximately
90 seconds, not a separate animation tutorial or a new rendering stack. The
[`pdoom-video`](https://github.com/mexicat/pdoom-video) is workflow inspiration
(storyboard, preview, export),
not a dependency. This brief changes no simulation or plan contract.
If the final cut must stay near 90 seconds, trim existing observation shots to
make room for the insert; do not silently turn a 92.6-second rough cut into a
longer final video.

## Story and edit

1. **Aberdeen — when to decline.** Retain the archived 15 May TD-message and
   detector playback. Capture the recorded Reader input/output pickup still
   listed in `deck/video-shot-list.md`. Replace the rough cut's provisional
   “comparison waiting” ending with the saved diagnostic ranking: P0 and P2
   tie, so the workflow makes **no plan recommendation**. Do not imply that
   Aberdeen proved there was nothing useful an operator could do in reality.
2. **Tuen Mun — when targeting may help.** In a short map-free comparison card,
   show the 15 April incident and the same frozen Lead plan set: P0 does
   nothing, P1 advises all eligible drivers onto Castle Peak Road, and P2
   advises 11%. On the saved 18-cell simulation grid, P2 ranks before P0 and
   P1 under the team's shared ranking rule; P1 ranks after P0. This is a
   **simulated candidate**, not an observed road saving. Avoid an animated
   route or vehicle trajectory unless Visuals receives a reviewed, run-bound
   route/trajectory asset.
3. **Close — one product behavior, two outcomes.** Ripple generates candidate
   options, tests them, and either declines to recommend or identifies a
   targeted candidate. A human operator remains in charge. Do not claim that
   the AI cannot hallucinate; the constraints and evaluator catch or reject
   unsupported proposals.

Suggested order: existing Aberdeen observation shots (0–71.5 seconds in the
current cut) → recorded model pickup and Aberdeen refusal (rework the current
71.5–92.6-second tail) → removable Tuen Mun card (15–25 seconds) → short close.
Re-time narration only after a reviewable edit exists; do not present the
current silent rough cut as a voiced final video.

## Required on-screen language

| Moment | Exact label or caption |
| --- | --- |
| Aberdeen map | **Archived TD messages and detector observations — 15 May 2026** |
| Reader pickup | **Recorded Qwen3:8b inference — not a live model call** |
| Aberdeen comparison | **Simulation diagnostic: no plan recommended (P0–P2 tie)** |
| Tuen Mun comparison | **Tuen Mun, 15 April 2026 — simulated candidate; baseline under review** |
| Tuen Mun plan card | **Targeted P2 (11%) ranks ahead of P0 and blanket P1 in this model** |
| Tuen Mun limit, on the same card | **Queue speed and recovery still under Simulation review** |

Do not put a percentage saving, CO₂ reduction, real-world improvement, live
deployment claim, or “hallucination-free” claim in the cut. If a numeric chart
is later approved, Data must supply its exact result path, denominator and
wording; Impact and Lead sign off before export. The 13 October shared ranking
rule favors Tuen Mun P2, but the stricter Tuen Mun-specific, predeclared
every-cell rule fails one cell. Keep both readings in the evidence and Q&A;
do not conceal the protocol difference.

## Source and asset handoff

| Owner and use | Repository-relative source / request |
| --- | --- |
| Visuals — preserve and edit | `deck/video-shot-list.md`, `deck/video-narration.srt`; local rough cut and its source manifest must be supplied with the review export. |
| Visuals — Aberdeen playback and Reader pickup | `data/demo_incident_messages.jsonl`, `results/reader/2026-09-29T1608_qwen3-8b.jsonl`, `evidence/demo/recorded-genai-bd-2026-10-13.html`; use the coverage and geometry qualifications in `docs/console-observed-playback.md`. |
| Data — Aberdeen refusal source | `results/rankings/lead-draft-20261013-b.json`, `docs/evaluator-lead-plans-2026-10-13.md`; `docs/incident-p0-verdict-2026-10-14.md` explains the incident-P0 limit. |
| Data — Tuen Mun plans and rank | `data/generated-plans/IN-26-02615-lead-capacity-oct15/`, `results/rankings/lead-capacity-oct15-p0x-merge-at-site.json`, `results/tuen-mun-lead-grid-oct15-p0x-merge-at-site/` (matched result/provenance pairs), `docs/tuen-mun-go-no-go-evidence-2026-10-15.md`. Check the Lead's capture card against the final result bundle and identify any revised figures or wording before export. |
| Lead — Tuen Mun capture aid | `evidence/demo/tuen-mun-result-card-2026-10-15.html` and its adjacent `.md` rebuilding guide. The card is generated from the saved plan/ranking/comparison files; keep its simulated-candidate banner and baseline limit visible in any crop. |
| Simulation — baseline verdict | `results/tuen-mun-p0-variants-oct15/p0-variants-report.md` and the pending lane/queue micro-test. State whether the current P0 remains a candidate or a changed P0 warrants matched P0/P1/P2 reruns. |

## 16 October switch

Visuals and Impact can build the insert now using the **simulated-candidate**
labels. At the Lead's 16 October claims review, Data supplies the final saved
ranking and Simulation supplies the P0 verdict. If a P0 change is adopted,
replace the card only after matched runs of the **unchanged 11% Lead plan set**;
if its ordering changes, update or remove the card. If no accepted P0 is ready,
the insert may still show the frozen *candidate* comparison with the visible
limit above, but must not be narrated as a measured benefit or an operator-ready
route recommendation. Aberdeen-only remains a complete export if the insert
cannot be supported or edited in time.

**Next files:** Visuals provides a timed storyboard/reviewable cut and names
missing assets; Impact adjusts the deck and limits slide to match the two-case
wording; Lead supplies the saved-result capture card, Data checks its figures
against the final result bundle, and Simulation gives the bounded P0 answer.
Lead reviews one combined cut and locks public wording at the
16 October decision before the 17 October internal submission target.
