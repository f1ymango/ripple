# Tuen Mun Lead plan set for the fresh grid — 15 October 2026

This is the Lead's experimental plan handoff for IN-26-02615, based on Data's
`data/tuen-mun-oct14` commit `9b434fd`. It does not change Aberdeen or claim a
measured benefit. Data's earlier 30% rehearsal outcomes were known before this
plan was selected, so the fresh-seed test is a confirmation of a revised
candidate, not a blind discovery.

## Files to evaluate

- Final plan set: `data/generated-plans/IN-26-02615-lead-capacity-oct15/`.
- Original logged D output: `data/generated-plans/IN-26-02615-lead-raw-oct15/`.
- Capacity rule: `data/lead-inputs/IN-26-02615_capacity-rule.json`.
- First-report transcription supplied to D: `data/lead-inputs/IN-26-02615_first-report.json`.
- Model call: `evidence/ai-log/2026-10-15.jsonl` (`qwen3:8b`).

D generated P0 with no action, P1 broadcasting Castle Peak Road to every
eligible Tuen Mun-bound driver, and P2 advising 80%. The 80% proposal was
bounded by a deterministic D parameter step; the model did not infer the
exit's spare capacity. Final P2 advises **11%** of that one OD group. P0 and P1
and their saved generation inputs are byte-identical between the two sets.

The rule uses the fixed-time Sham Tseng exit's **estimated** 260 vehicles/hour
spare from Data's sensitivity, 2,082.7 eligible vehicles in the 48-minute
action window (2,603.375/hour), 70% maximum tested compliance, and a 20%
capacity reserve. `0.8 × 260 ÷ (2,603.375 × 0.7) = 0.1141`; round down to
hundredths, yielding 0.11. This is a conservative candidate-selection rule,
not an observed junction capacity or a proven optimal share. The manifest in
the final plan directory records the source hashes and calculation.

P1 and P2 start at TD's 17:59 report; the common context ends at 18:47.
There is no early detector action, retrospective 18:17 cutoff, signal change,
sign effect, or Route 3 advice. The current D/E contracts do not express a
P2-only dynamic cutoff. Castle Peak Road's actual scenario detour uses 34
SUMO edges classified `highway.primary` or `highway.motorway_link`, with no
`highway.residential`/`highway.living_street` edges; that is the narrow basis
for accepting Data's `residential: false` in this experiment. It is not a
land-use survey.

## Fresh test requested of Data and Simulation

Run the **final** plan set, not the raw 80% set, on fresh seeds 2029–2031,
compliance 0.3/0.5/0.7, and both existing Sham Tseng signal designs. Compare
each plan with the matching P0 using Data's already published delay measure,
including the longer Castle Peak Road drive and outside-delay sensitivity.
Report every cell, vehicles diverted, exit queues, waiting to enter,
teleports, and P0 detector/queue checks. Keep Simulation's predeclared P0
variants as a parallel diagnostic; do not change this plan set after seeing
the fresh-grid results.

If P2 wins the team's every-cell rule, it becomes a candidate for the 16 Oct
go/no-go review, not an automatic public saving claim. If it fails, retain
Aberdeen as the submission fallback. P1 remains the broadcast comparator;
under the shared contract it is necessarily full-share advice here.
