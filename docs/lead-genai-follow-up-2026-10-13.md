# Lead GenAI follow-up — 13 October 2026

## Decision boundary

The [13 October generated plan set](../data/generated-plans/IN-26-03365-lead-draft-20261013-b/)
remains a retrospective candidate demonstration. It has not been evaluated
against an accepted incident P0. Data and Simulation's [joint NO-GO](evaluator-p0-go-no-go-2026-10-09.md)
continues to block public plan ranking, recommended-route highlights,
evaluated-vehicle animation and traffic-benefit claims. A functioning local
briefing writer or offline evidence page does not change that decision.

The 15 October pack should proceed with observed incident playback, recorded
Reader and Plan Generator evidence, and only visibly labelled fixture UI where
needed. The 16 October results/claims freeze remains provisional (hour not
agreed); the internal submission target remains 17 October.

## F — format repair and bounded model trial

The internal `src/briefing/writer.py` model payload now presents the selected
action meanings and permitted metric-token names/units. Complete result values
remain in code for ranking, provenance checks and token substitution. The
file-based F prompt now specifies one entry per supplied sign, mandatory
uncertainty placeholders and draft guidance wording. The public JSON contracts,
numeric gate, provenance checks and `write_briefing` API were not changed.

The original fixture triplet and sidecars passed the model-free preflight.
Focused F/plan/helper/adapter checks passed: **71 tests**. The next live
`qwen3:8b` trial was limited to two invocations and three calls; no further
attempt is planned in this execution. Temperature was 0, seed 42, output cap
2,048 tokens and thinking was disabled. The exact prompts and replies are in
[`evidence/ai-log/2026-10-13.jsonl`](../evidence/ai-log/2026-10-13.jsonl)
(final raw-file SHA-256
`49dc7e73209d56de1987d904253e8c5f8646200f2726162cccc92ad6203572d6`).

| Call (13 Oct HKT) | Logged duration | Outcome |
| --- | --- | --- |
| 13:11:27 | 26.81 s | Rejected duplicate fixture sign ID; no output saved. |
| 13:11:54 | 7.94 s | Schema and token checks passed; saved synthetic draft `mock_genai_briefing_20261013_token_a.json`, then **rejected on semantic review**. It claims reduced congestion/potential emergency travel time effects and gives drivers an instruction to review rather than candidate route advice. |
| 13:12:47 | 9.40 s | Final targeted invocation; saved synthetic draft `mock_genai_briefing_20261013_token_b.json`, then **rejected on semantic review**. It claims some users' travel time increases without evidence, adds unsupported residential/emergency audiences, and corrupts the Chinese sign's route name. |

Both saved files are under `tests/fixtures/` and begin `mock_`. Raw-file
SHA-256: `token_a` =
`478c7e187e2ac6a24799d236946bd89fe272c4c0f0dca495a4af10e5ba5cddbb`
and `token_b` =
`924012942efe5f1da6ce4060de0a31194516cbaf55149f38c37eb3036fb5064a`.
Neither file is an accepted briefing or a gold example.
Their displayed metric values are synthetic fixture values. Passing structural
validation did not establish semantic accuracy. Human bilingual sign-off is
still pending, and no briefing for the real incident was generated.

## Recorded B/D capture aid

The [offline page](../evidence/demo/recorded-genai-bd-2026-10-13.html)
displays the two archived TD messages beside their saved Reader extractions
and the three already-generated candidate plans. It embeds the selected
source paths, call times, raw-file SHA-256 hashes, retrospective-context
qualifiers, the P1 title mismatch, assumed signal control and P0 NO-GO.
Its SHA-256 is
`46b4d6d4cbe65f3c5a1b54a9ada18ab5db394df38b24c9e86bc49f4f53e7a195`.
The [exporter and rebuild guide](../evidence/demo/README.md) check the saved
outputs against their logged calls and refuse to overwrite an earlier page.
One 1440-pixel desktop first-viewport rendering was inspected for bilingual
side-by-side readability and persistent labelling. Static tests cover escaping,
the required qualifications and absence of external assets. The full page
and mobile layout were not visually reviewed; Visuals must still capture and
edit footage. No new console playback or simulator run was made for this aid.

Verification: F/plan/helper/adapter focus, **71 passed**; exporter focus,
**8 passed** including two tamper regressions; complete repository suite on
the host, **598 passed, 1 skipped**.
The first sandboxed full-suite attempts were obstructed by restricted temp
directories and loopback sockets; the host rerun passed. No new dependency,
public JSON contract or simulation acceptance gate was changed.

## Available fallback paths

| Condition | Presentation material | Claim boundary |
| --- | --- | --- |
| Local Ollama is unavailable or F is rejected | Saved Reader input/output/log and generated plan input/output/log | Recorded inference; no fresh F success claim |
| Accepted SUMO incident comparison is absent | Existing observed console plus recorded B/D evidence | No plan ranking, route highlight, trajectory or delay/CO₂/travel-time saving |
| Optional network or basemap is unavailable | Recorded B/D evidence page and existing saved screenshots | No claim that road geometry or full console playback is offline |
| Bilingual F output remains unusable | Existing `tests/fixtures/mock_recommendation/` operator-workflow demonstration | Clearly synthetic UI capability; not a new model-written briefing |
| Final owner media is not delivered | Reviewable evidence page and Markdown slide/source pack | Source material only; not a finished video or deck export |

The recorded Reader output for message `138270` retains its imperfect
free-text direction note. The D context contains later-known incident details
and an assumed signal action. Neither should be silently corrected in captured
material. The existing fixture workflow already demonstrates display and
operator approval behavior; no new template substitute is needed.

## Remaining delivery work

- **Data/Simulation:** assess whether the exact new P0/P1/P2 files can be run
  diagnostically and flag unsupported actions. Any new result bundle needs its
  own original provenance and explicit joint scientific review before a public
  comparison. There is no claim that new results are due or accepted.
- **Visuals:** capture recorded B/D inference with the above labels, and supply
  an accessible playable cut, captions and source manifest. Existing cut
  timings should change only against the edited media.
- **Impact:** provide editable slides and a reviewable export linked to the
  evidence manifest. Leave unsupported benefit and operating-cost figures
  unmeasured.
- **Lead + Impact:** confirm delivery format, named uploader, prototype/deck/
  video access and the submission receipt. These remain unconfirmed.

This owner note is drafted in the repository and has **not been sent**.
