# Ripple — project status and interim-report summary

**Reviewed:** 3 October 2026 (Hong Kong time). **Official interim deadline:** 4 October; internal target: 3 October.
**Reviewed main:** `962a5b3f03f628be900f19d0271c8cc7fe7c19d3` after the merges below.

## Summary suitable for the interim report

Ripple has progressed from individual prototypes to a tested set of components for an Aberdeen-corridor incident co-pilot. The data pipeline ingests public Transport Department detector readings and bilingual incident messages, the Incident Reader produces structured records, and the operator console replays observed traffic conditions. Initial plan-generation, constraint-validation and bilingual-briefing components are implemented. The central remaining dependency is an accepted traffic baseline and a completed evaluator: no validated end-to-end plan comparison or measured reduction in delay or emissions is available yet.

The data layer covers 28 corridor detectors and handles missing archive snapshots, zero-vehicle speed placeholders and incident status changes. Combining the three archived Special Traffic News feeds increased complete incident timelines from 68% to 85% in the documented March–September sample. The selected demonstration incident is IN-26-03365 on 15 May, with IN-26-06391 as backup. The candidate ranking needs refreshing after subsequent screening changes; archive gaps must not be described as proven random or unbiased.

The Reader has been evaluated on 100 labelled messages. Its original held-out all-field accuracy was 50% on 80 citywide messages and 75% on 20 corridor messages. Following prompt and label corrections, development scores reached 75% and 85%, respectively; these are not fresh held-out results. An October prompt experiment performed worse and was not adopted. Reader output files now resist accidental overwriting, protecting experimental evidence.

The SUMO twin runs and has undergone detector-placement, connectivity, lane-scope and demand diagnostics, but validation remains below target. In the controlled 2 October comparison, removing the global vehicle speed ceiling changed the proportion of count bins meeting GEH < 5 from 66.53% to 66.94%, against a target of at least 85%. Speed MAPE worsened from 36.94% to 41.36% on 296 common bins, against approximately 15%. Teleports fell from 68 to 53, but these improvements do not establish an acceptable baseline. The provisional network and supporting local inputs are not a portable, reviewed release.

A simplified cell-transmission fallback is implemented on an open branch. Its saved result reports GEH < 5 for 97.1% of 205 internal count bins and 17.8% speed MAPE across 252 internal speed bins. The broader 242-count-bin score includes demand-input detectors. These are provisional diagnostics: the run injects a closure at 08:54 while scoring a nominal pre-incident window through 08:55. A separate no-closure calibration is required. Equality with an ordinary-day speed reference is not a mathematical error floor or proof of zero model error. Diversion and incident queue recovery are not yet validated.

The Plan Generator and Briefing Writer have offline tests, schema checks, constraints and result-provenance verification. They still require reviewed route/context inputs and real comparable evaluator outputs. The console already provides detector maps, speed indicators and archived timeline playback. Its proposed recommendation, briefing and operator-decision workflow remains under review. One qualitative minibus-driver interview supports further investigation of trusted route information and local wording; it does not establish general driver preferences or quantified benefits.

## PR decisions

| PR | Decision | Reason |
|---|---|---|
| [#36](https://github.com/f1ymango/ripple/pull/36) | Merged | Reader run preservation and regression tests; experiment evidence correctly distinguished from held-out evaluation. |
| [#38](https://github.com/f1ymango/ripple/pull/38) | Merged | Simulation report states unmet targets and pending comparisons. Linked evidence at commit `be7bd65` was retrieved and checked. |
| [#40](https://github.com/f1ymango/ripple/pull/40) | Merged | Visuals contribution and screenshot accurately distinguish observed playback from unmeasured simulation benefits. Capture has a disclosed clipped right edge. |
| [#35](https://github.com/f1ymango/ripple/pull/35) | Held | Existing calibration/scenario findings remain unresolved; branch also conflicts with main. |
| [#37](https://github.com/f1ymango/ripple/pull/37) | Held | Unsupported causal/benefit claims, assumptions presented as observed closure facts, a non-rendering image placeholder and incorrect relative links. |
| [#39](https://github.com/f1ymango/ripple/pull/39) | Held | Report repeats unresolved fallback claims and overstates evidence on missingness and plan-ranking reliability. |
| [#41](https://github.com/f1ymango/ripple/pull/41) | Held | Unconditional Unix-only `fcntl` import prevents console startup on Windows. CI also fails its file-opening hygiene test. |

Specific corrections before re-review:

- **#35:** use a separate no-closure calibration; regenerate results rather than edit them; call the speed comparator an ordinary-day reference; disclose retrospective closure hypotheses; restrict the CLI to its implemented incident or supply explicit scenario configuration. These findings were already recorded in [the 30 September review](https://github.com/f1ymango/ripple/blob/962a5b3/docs/2026-09-30-lead-follow-up.md).
- **#37:** distinguish observed low flow from a confirmed physical closure/onset; describe spillover and benefits as hypotheses pending evaluation; keep interview findings scoped to one participant. Remove or replace `image_agent_tag_3766287884585980765` and correct links relative to `docs/`. Vehicle-class constraints require an explicit future design decision.
- **#39:** remove claims that a 0.2 km/h difference proves random/unbiased gaps, that a constant-speed comparator is an error floor, or that common assumptions guarantee reliable plan rankings. Label closure timings as hypotheses. Do not present the fallback as accepted calibration before #35 is corrected.
- **#41:** implement cross-platform audit locking and test on Windows. The CI failure at `render_replay.py:138` concerns a binary `Path.open("rb")`; the hygiene checker misclassifies it, so adding text encoding to that binary open would be incorrect. Also bind replay trajectories to evaluated simulation inputs: recording hashes of arbitrary supplied FCD files alone does not prove they belong to the compared runs.

## Immediate priorities

1. Impact and Lead: finish evidence-safe Sections 1 and 5, correct and integrate Data's contribution, refresh the stale contribution checklist, and confirm uploader/submission receipt. The merged report is still a working draft, not a submitted final report.
2. Data and Simulation: make the 4 October SUMO/fallback decision using comparable no-closure diagnostics. Separately agree incident lane/timing assumptions and demonstrate queue recovery.
3. Data/E: implement comparable P0/P1/P2 runs and provenance, then compliance/clearance sensitivity. Real route/context inputs are prerequisites for D/F integration.
4. Visuals: fix Windows startup and complete tested operator workflow; retain observed-data playback until accepted plan outputs exist.
5. Team: protect the 14 October results freeze, then finish the demonstration video, deck and remaining interview evidence ahead of the 18 October final deadline.

## Verification and limits

- Original main: **373 tests passed** on this Windows PC using the existing Python 3.13 environment.
- Combined #36/#38/#40 integration: **376 tests passed**, with one Altair deprecation warning. The resulting file tree exactly matches remote main at `962a5b3`.
- Post-merge [GitHub CI on final main](https://github.com/f1ymango/ripple/actions/runs/37104194864) completed successfully.
- Confirmed the Windows `fcntl` import failure independently; inspected #41's CI failure (395 passed, one hygiene failure).
- Reviewed saved simulation/Reader evidence and PR changes. No new live LLM, SUMO or fallback replay was run; traffic figures above are attributed saved results, not newly reproduced measurements.
- No shared contracts, dependencies or generated results were changed. PR review comments/messages were not posted to teammates. The original checkout and its untracked `AGENTS.md` were preserved; integration tests ran in an isolated worktree.
- The source diff contains two minor Markdown trailing-whitespace findings in #38; these do not affect the test result.

Primary evidence: [merged interim draft](https://github.com/f1ymango/ripple/blob/962a5b3/docs/interim-report.md), [Reader score history](https://github.com/f1ymango/ripple/blob/962a5b3/data/labelled_incidents/LABELLING.md), [2 October simulation diagnosis](https://github.com/f1ymango/ripple/blob/be7bd65/docs/calibration-progress-2026-10-02.md), and [fallback result under review](https://github.com/f1ymango/ripple/blob/037a4bc/results/fallback/replay_20260515.md).
