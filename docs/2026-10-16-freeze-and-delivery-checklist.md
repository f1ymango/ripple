# 16 October claim freeze and final delivery — Lead checklist

**Lead decision, 16 October HKT:** the saved two-incident result set and its
public claims are frozen. The internal delivery target is 17 October. The
organiser's [2026 final-submission instructions](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/)
set the hard deadline at **18 October 2026, 23:59 HKT**. The actual submission
link and account permissions still need an uploader check. An unauthenticated
open of the linked SharePoint upload redirected to HKU Microsoft sign-in;
confirm the named uploader can reach the actual upload before the deadline.

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
| Impact | Carry Mark's merged [15 Oct slide draft](https://github.com/f1ymango/ripple/pull/70) through a two-case consistency pass. Review the [16 Oct Lead Q&A source copy](../deck/qa-sheet.md), reconcile the open [Q&A PR #69](https://github.com/f1ymango/ripple/pull/69), and sign off presenter wording before export. | Markdown slides and Lead Q&A source updated; Impact editorial review pending |
| Lead | Review the [single-cell F draft](../data/generated-briefings/IN-26-02615-p2-demo-oct16.json) before any public use. Its Chinese text contains the literal drafting instruction `保留正負號`, and its −5% token describes one cell, not the 18-cell ranking. Preserve the original generated artifact; omit its text from the deck/video unless a human-corrected version passes operator and language review. | Lead content review: **not approved for public use as written** |
| Impact | Export an editable deck and reviewable pitch file covering both cases and the five judging criteria; check visual readability, captions and citations. | No rendered deck in the repository at this checkpoint |
| Visuals | Deliver a balanced playable two-case cut with captions and a source manifest. Show Tuen Mun's comparison panel/result card, not the Aberdeen map. | No playable final video in the repository at this checkpoint |
| Lead + uploader | Confirm the named uploader and access to the live deck upload; test every prototype/video link from a viewer account; submit the locked deck once, then preserve the receipt. | Pending; no uploader or receipt recorded |

## Organiser's 2026 upload rules — checked 16 October

- **Pitch deck:** one file per team, `.ppt`, `.pptx` or `.pdf`; no online or
  cloud-based slide deck. The first slide must show the team name, project
  title, thematic track, a description of at most 30 words, and every member's
  full name and university. Name the file `Team Number – [Team Name]`, using
  the team's actual assigned number and name. The deck must be primarily in
  English; translate any other-language content into English.
- **Prototype proof:** embed the demo video, application, technical or GitHub
  links inside that deck. A working prototype is important to selection; do
  not leave the only proof in a separate message or an inaccessible local file.
  Check playback and sharing permissions from an account other than the
  uploader's. The final pitch uses the uploaded deck; teams cannot use their
  own laptops or devices for the presentation.
- **Upload is irreversible:** the organiser says slides are locked once the
  upload button is pressed. Finish the source/caption and cover-slide review
  before submitting. Missing the deadline or violating the instructions is
  an automatic disqualification risk. If a technical submission failure occurs,
  the [official page](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/)
  provides an emergency email route **before** the deadline; this is not a
  substitute for a normal upload.
- **Optional Tencent/WorkBuddy prize:** a separate WorkBuddy-use report may be
  submitted as a PDF with the same first-page identity fields and filename
  pattern. This is optional for the main competition and should not displace
  the deck and prototype-proof delivery.

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

## Mark's Thursday handoff review

The merged [PR #70](https://github.com/f1ymango/ripple/pull/70) delivered the
two-incident **Markdown slide draft**, including the frozen 11% Tuen Mun plan
and saved comparison. It was not a rendered deck or video. This wrap-up branch
keeps its useful structure while correcting the archived detector gap (not a
proven live early alert), Aberdeen's P0/P2 tie (not proof that P0 is optimal),
and the source review of the unsourced signal (not an automatic evaluator
detection). It also adds Simulation's Tuen Mun queue-limit caption.

Mark's separate [Q&A PR #69](https://github.com/f1ymango/ripple/pull/69) is
still open with changes requested: it repeats early-alert and P0-optimal
language, implies P2 wins each of 18 conditions, calls the confirmed freeze
provisional, and omits the P0 queue limitation. Lead's current
[two-case Q&A source](../deck/qa-sheet.md) addresses those points, but Impact
must reconcile the PR and approve presenter copy before export. The current
video shot list and timed narration also describe only the older Aberdeen cut;
Visuals owns the two-case recut and retiming before export.
