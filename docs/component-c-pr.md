# Component C: corrected demand loading, source audits and diagnostic video

## Summary

- Fix departure ordering and explicitly report origin-suspension demand removal.
- Harden lane audit cache provenance and conflicting-reading handling.
- Add bounded pre-incident replay, source-hashed results and handoff notes.
- Include the full traffic-only MP4 and run manifest.

## Evidence and limits

Pre-incident replay completed 4,500 seconds: 66.94% GEH pass (242 bins),
36.84% speed MAPE (296 bins), 123 teleports. Full traffic-only replay completed
10,500 seconds; its video labels the provisional network and no closure assumed.
Two focused tests passed earlier; no full suite rerun with the latest changes.
The MP4 was fully decoded and a frame inspected.

This is not a validated baseline. Physical placement/lane-scope review and
Data/E's initial partial-closure assumption remain open. No accepted full
incident P0 validation exists. Lead retains the merge decision.

## Invalid historical artifacts

`results/twin/invalid/partial-lane-index-0-evaluation.json` and
`results/twin/invalid/partial-lane-index-1-evaluation.json` are preserved unchanged
for audit history only. SUMO ignored routes because their departure times were
unsorted. Their scores MUST NOT be used for validation, comparisons or claims.
These files do not represent an accepted initial-lane choice.

Downloaded caches, raw FCD and provisional generated network/loop files remain
in ignored local storage. They are not reviewed shared network deliverables.
