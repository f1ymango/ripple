# Two-case demo handoff — Lead, revised 15 October 2026

## Decision and presentation goal

**Make Aberdeen and Tuen Mun co-leads.** Give each roughly half of the incident
demonstration time in the video and one equally prominent case panel or slide in
the deck. Aberdeen shows Ripple declining to recommend when its tested options
tie. Tuen Mun shows the positive prototype result: targeted advice ranks ahead
of doing nothing and blanket advice in the saved simulation. The contrast is the
product story: **know when to hold back and when to target a response**.

This replaces the earlier plan to append Tuen Mun as a 15–25-second afterthought.
Visuals' 92.6-second silent Aberdeen rough cut is useful footage, not a locked
edit. Recut it into two balanced chapters. Approximately 90 seconds is the
team's working video target, **not an organiser-imposed length**. The official
[2026 final-submission instructions](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/)
require a pitch deck and prototype proof by **18 October, 23:59 HKT**; a demo
video, application or technical link can serve as proof within the deck. The
deck is locked after upload, and the team cannot rely on its own laptop at the
final pitch. Build a self-contained, pre-tested deck even if the video link
fails to play. The final stage allows a five-minute pitch plus Q&A; the video
must support that pitch, not consume it.

## Video edit: two equal chapters

| Approximate time in a 90-second cut | Story | What to show |
| --- | --- | --- |
| 0–6 s | Hook | Ripple as an incident co-pilot: read, draft, test, brief an operator. |
| 6–43 s | **Aberdeen: hold back** | Archived 15 May TD message and detector playback; the recorded Reader input/output; the P0–P2 tie and no-recommendation verdict. |
| 43–80 s | **Tuen Mun: target** | Archived 15 April incident context; Castle Peak Road as the alternative; AI-drafted options refined by a deterministic capacity bound; the matched P0/P1/P2 comparison, with targeted P2 first and blanket P1 worse. |
| 80–90 s | Close | One operator workflow, two appropriate outcomes; human review remains the final step. |

These are editing proportions, not exact timestamps. If pacing needs more time,
shorten repeated Aberdeen observation shots before cutting the Tuen Mun plan
comparison. Re-time `deck/video-narration.srt` only after a reviewable recut;
the existing rough cut is silent.

The Tuen Mun comparison should be visually direct: three bars or cards with
P0 as the zero reference, P1 at **+37.3%** and P2 at **−4.3%** in the same
modelled E-delay measure. Label the chart **Prototype simulation, 18 scored
conditions**. A small adjacent note can say that P2 remains **−3.7%** when
the longer Castle Peak Road drive is charged under Data's four-minute
outside-network sensitivity. Do not mix the −3.7% adjusted P2 figure with the
unadjusted +37.3% P1 figure on one unlabelled scale. The positive result is
modest, which is fine; the contrast with blanket diversion is strong.

Keep the GenAI attribution exact: D drafted candidate actions, the Lead's
deterministic capacity step bounded the Tuen Mun P2 share to **11% before the
fresh-seed grid**, and E tested the resulting plans. Do not say the model
independently discovered an optimal 11% share or calculated the traffic
benefit. P0 is the no-advice baseline; P1 is the fixed blanket-advice
comparator, not a plan being tuned for performance. Use the existing recorded
inference, not a staged live-model call.
Do not animate a highlighted route or evaluated vehicles without a route or
trajectory asset bound to the reviewed run.

The [`pdoom-video`](https://github.com/mexicat/pdoom-video) reference is
workflow inspiration for storyboard, preview and export, not a dependency or a
request to rebuild the rendering stack.

## Deck and spoken pitch

- Give Aberdeen and Tuen Mun **equal space within the case-study section**:
  one matched slide or panel each. This is not a request to spend half of the
  entire five-minute pitch on each incident; the deck still needs the problem,
  working GenAI workflow, feasibility, impact and implementation plan.
- Lead with the outcome on the Tuen Mun panel: **targeted advice lowered
  modelled delay by about 4% on the saved comparison; telling everyone to
  divert made it worse**. Put the exact measure and source in a readable
  caption. On the Aberdeen panel, lead with the tie and Ripple's refusal to
  endorse a plan. Together they demonstrate selection, not just abstention.
- Show prototype proof inside the submitted deck: a console/Reader capture,
  the Tuen Mun comparison and an accessible video or technical link. Keep
  essential screenshots in the deck so reviewers are not dependent on a live
  service or network connection. Check the uploaded format and playback before
  the one-way submission.
- The mandatory first slide needs the team name, project title, thematic
  track, a description of at most 30 words, and all members' full names and
  universities. Use the organiser's required filename and `.ppt`, `.pptx` or
  `.pdf` format; do not submit cloud-hosted slides as the deck.

## Public wording and technical backup

| Use in the main cut/deck | Keep precise in the evidence, appendix and Q&A |
| --- | --- |
| **Aberdeen:** “With no clear winner in this comparison, Ripple makes no plan recommendation.” | This is a diagnostic simulation verdict, not proof that no real-world intervention could ever help. The playback is archived, not a live alert. |
| **Tuen Mun:** “In our prototype simulation, targeted advice ranks first: about 4% less modelled delay than doing nothing; blanket advice increases delay.” | Saved team ranking: P2 −4.31% versus P0, P1 +37.3% versus P0 over 18 scored cells; the four-minute detour-inclusive sensitivity gives P2 −3.70%. These are model outputs, not observed road savings. |
| **Workflow:** “AI drafts options; constraints and capacity checks shape them; the twin compares them; an operator decides.” | The 11% share was capacity-bounded before the fresh runs, not selected by an autonomous optimisation or proof of a global optimum. |

Put **“Prototype simulation — not measured road saving”** adjacent to the
Tuen Mun chart, not buried in a later disclaimer. Avoid “hallucination-free,”
“proven real-world saving,” “live early warning,” and an operator-ready route
recommendation. This is enough context for the main story without turning the
video into a debugging report.

Prepare a concise, candid Q&A/appendix answer rather than a sequence of bug
slides: the current Tuen Mun P0 passes the team's headline validation v2 on
the scored seeds, but its queue moves too fast and clears early, so Simulation
has not accepted it for a measured-benefit claim. The Tuen Mun-specific
predeclared every-cell rule fails one cell; the team's earlier shared ranking
rule, used by E/F/the console and Aberdeen, ranks P2 first. State both rules
if asked and keep the full source paths below. Do not change the ranking rule
or hide the difference.

## Source and asset handoff

| Owner and use | Repository-relative source / request |
| --- | --- |
| Visuals — recut | `deck/video-shot-list.md`, `deck/video-narration.srt`; local rough cut and its source manifest. The shot list is Aberdeen-only and must be updated for the co-equal cut. |
| Visuals — Aberdeen playback and Reader pickup | `data/demo_incident_messages.jsonl`, `results/reader/2026-09-29T1608_qwen3-8b.jsonl`, `evidence/demo/recorded-genai-bd-2026-10-13.html`; follow the source distinctions in `docs/console-observed-playback.md`. |
| Data — Aberdeen verdict | `results/rankings/lead-draft-20261013-b.json`, `docs/evaluator-lead-plans-2026-10-13.md`, `docs/incident-p0-verdict-2026-10-14.md`. |
| Data — Tuen Mun plans and ranking | `data/generated-plans/IN-26-02615-lead-capacity-oct15/`, `results/rankings/lead-capacity-oct15-p0x-merge-at-site.json`, `results/tuen-mun-lead-grid-oct15-p0x-merge-at-site/`, `docs/tuen-mun-go-no-go-evidence-2026-10-15.md`. Check the public figures against the final saved bundle before export. |
| Lead — comparison capture aid | `evidence/demo/tuen-mun-result-card-2026-10-15.html` and its adjacent `.md` guide. The existing card is a provenance-rich **source/capture aid**, not the required final visual treatment; Visuals may design a cleaner result-first graphic while retaining the modelled-result label and exact numbers. |
| Lead — operator briefing draft | `data/generated-briefings/IN-26-02615-p2-demo-oct16.json` is F's provenance-checked bilingual draft for the **single** packed 50%-compliance, seed-2029 condition. Its −5% token is that condition's E result, not the 18-condition −4.3% finding. F/console use logical `results/runs/` source aliases; the physical verified files are under `results/demo-oct16/tuen-mun/runs/`. Human language and operator review are still required before presenting it as approved advice. |
| Simulation — P0 verdict | `results/tuen-mun-p0-variants-oct15/p0-variants-report.md`. Data reports that the lane/queue stress change improved queue speed but failed flow and recovery, so it was not adopted as P0. Review that result and report whether a flow-valid replacement arrives before the claim lock; any replacement needs matched P0/P1/P2 reruns. |

## 16 October claim lock and owners

The working edit is **50/50 now**, using the saved Tuen Mun result as a
clearly labelled prototype-simulation candidate. Data's 15 October stress
test did not replace the baseline, so the current pack remains the working
comparison. Do not wait for a perfect incident replay before making the edit.
At the 16 October claims review:

1. **Data and Simulation** give the latest P0 verdict and saved ranking. If a
   corrected P0 is adopted, rerun the **unchanged 11% Lead plan set** on
   matched inputs before replacing the chart or upgrading any claim.
2. **Lead** locks the exact Tuen Mun wording. Keep equal representation if the
   positive comparison still stands, even if it must remain explicitly
   labelled a simulation candidate. If a new matched result reverses the
   ordering or invalidates the comparison, replace the positive chart rather
   than narrating an obsolete win.
3. **Visuals** delivers one timed, reviewable two-case cut and updates the shot
   list; **Impact** updates the case-study slides and prepares the short Q&A
   answer. The remaining deck work targets internal completion on 17 October,
   before the organiser's 18 October upload deadline.

Neither case should be presented as live traffic control. The competition
pitch should foreground the working prototype and the strongest result while
remaining exact about what was observed and what was simulated.
