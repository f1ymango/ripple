# Video and deck evidence review — 8 October

Local review notes for Lead and Impact; no message has been sent. Checked
against main `34e0829` after PRs #49 and #50. The Visuals shot list is corrected
in this branch. Other deck files remain available for their owners to revise.

| Finding in the merged draft | Verified evidence | Requested alignment |
| --- | --- | --- |
| Reader figures 75% citywide / 85% corridor cite the October 1 score in `slides.md`, `qa-sheet.md`, `real-vs-simulated.md`. | That October artifact has all-field scores 50/80 (62.5%) citywide and 12/20 (60%) corridor. The 75% / 85% scores are 60/80 and 17/20 in `results/reader/2026-09-25T0048_qwen3-8b_score.json`. | Use the correct September source and explicitly call these development scores after prompt/label corrections. They are not a fresh held-out evaluation. Retain the initial held-out 50% / 75% context from `data/labelled_incidents/LABELLING.md` and the interim report. |
| The previous video shot list labelled `aberdeen-diagnostic.gif` as 07:55–08:55 pre-incident footage. | `results/twin/README.md` identifies the GIF as an earlier September IN-26-06481 run, stopped after teleport warnings, with zero scoreable detector bins. | Keep it out of the May observed-playback cut. An optional separate excerpt needs an explicit September/unvalidated label. |
| The previous raw-message shot referenced `closed-lanes_AID01104_20260515-0840_1010.json`. | That artifact infers phases from detector readings and an ordinary-day rule. Archived TD prose is in `data/demo_incident_messages.jsonl`. | Use the message source for the report shot; keep inferred physical phases separate from publication timestamps. |
| Some slides/README/Q&A wording expects full-closure validation or new metrics after the freeze. | `docs/04-plan.md` fixes results on 14 October, targets internal submission on 17 October and identifies the 18 October deadline. It also retains the 9 October scope decision. | Do not promise validation by date or treat the freeze as permission to add unaccepted metrics. Claims missing acceptance at freeze remain unmeasured. |

As checked on 8 October, PR #46 remains open with the Lead's 5 October
changes-requested review. Passing CI does not mean that its proposed baseline
is accepted. The latest main additions are deck documents; they do not supply
a newly accepted P0/P1/P2 bundle or evaluated FCD provenance.

Reader percentages above are quoted from saved scoring outputs, not newly
computed simulator metrics. This review changes neither results nor contracts.
