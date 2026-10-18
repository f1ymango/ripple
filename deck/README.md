# Presentation Deck & Evidence Pack

This folder contains the [current ten-slide PowerPoint review deck](ripple-visual-demo-pitch-2026-10-18-v17-detectors-review.pptx), the [90-second narrated two-case video](../docs/video/ripple-two-case-website-demo-2026-10-18-v17-detectors-narrated.mp4), and earlier source drafts. The video is embedded on slide 5. The [submission media index](submission/README.md) identifies the current files and upload gates. Neither a final upload nor a receipt is recorded here.

---

## 1. The Five Criteria (20% each)

Every slide and artifact is traceable to one of these core criteria:

| Criterion | Owner | Material Source |
| :--- | :--- | :--- |
| **Convincing framing of problem** | Impact | `docs/05-pitch.md` §1, §3 |
| **Prototype / demo** | Visuals + Lead | Demo Video, Console, `results/twin/` |
| **Appropriate technical component** | Lead | GenAI jobs, `results/reader/` benchmark scores |
| **Feasibility and impact** | Impact | `deck/costing.md` |
| **Sustainability and ethics** | Impact | Constraint thresholds, `deck/qa-sheet.md` |

### Current ownership and status

| Area | Owner | Evidence status |
| :--- | :--- | :--- |
| Problem, pitch and evidence pack | Impact | Markdown sources and a ten-slide review deck are present; final cover, playback and upload checks remain |
| Observed incident prototype | Visuals + Lead | Aberdeen archived playback is locally rehearsed; it is not a live early-warning demonstration |
| Reader / GenAI evidence | Lead | Saved input, output, call log and evaluation exist; video pickup remains |
| Plan Generator | Lead | Saved drafts exist for both cases. A deterministic capacity rule capped Tuen Mun P2 to 11% before the fresh-seed grid; the AI did not optimise that share ([handoff](../docs/2026-10-15-two-case-demo-handoff.md)). |
| Briefing Writer | Lead | A [Tuen Mun single-cell bilingual draft](../data/generated-briefings/IN-26-02615-p2-demo-oct16.json) is provenance-bound, but Lead's 16 Oct content review found a literal drafting instruction in the Chinese output. Keep it out of public copy until human-corrected and operator-reviewed ([checklist](../docs/2026-10-16-freeze-and-delivery-checklist.md)). |
| Evaluator and provenance | Data | [Two-case pack](../results/demo-oct16/) has comparable runs, sidecars and saved verdicts: Aberdeen tie/refusal, Tuen Mun model-ranked P2. |
| Simulation validation | Simulation | Tuen Mun is accepted for a labelled modelled-candidate comparison, not a measured road-saving claim; its queue moves too fast and clears early ([final call](../docs/tuen-mun-simulation-final-call-2026-10-15.md)). |
| Video | Visuals | A narrated 90-second two-case MP4 and source record are committed; venue playback remains unchecked ([handoff](final-visuals-handoff-2026-10-18.md)). |

---

## 2. File Inventory & Index

| File | Description | Status & Freeze Boundary |
| :--- | :--- | :--- |
| [slides.md](slides.md) | Two-case slide structure aligned with 5 scoring criteria | Mark's Markdown draft, corrected on the Lead wrap-up branch; export pending |
| [real-vs-simulated.md](real-vs-simulated.md) | Observed sources, modelled comparisons and unsupported benefit claims | Two-case boundary updated; final Impact editorial review pending |
| [costing.md](costing.md) | Resource questions and BCR limitations | Draft; operating cost not measured |
| [qa-sheet.md](qa-sheet.md) | Two-case technical Q&A and known limitations | Lead updated the frozen-claim source copy on 16 Oct; Impact must reconcile [PR #69](https://github.com/f1ymango/ripple/pull/69) and give a final presenter review before export |
| [video-shot-list.md](video-shot-list.md) | Current two-case shot list and source boundaries | V17 narrated cut delivered |
| [submission-manifest.md](submission-manifest.md) | Deliverable, evidence, owner and claims inventory | Updated for the delivered deck/video and remaining upload checks |
| [submission/README.md](submission/README.md) | Current media paths and checksums | One-file upload handoff; not a receipt |

---

## 3. Key Dates & Governance

- **Sat 3 Oct**: Interim report submitted
- **Thu 15 Oct**: Two-case evidence pack and Markdown slide draft received; deck/video exports not yet recorded here
- **Fri 16 Oct**: **Results/claims frozen** — the saved 11% two-case pack and labelled claims are locked
- **Sun 18 Oct**: Visuals delivered the ten-slide review deck and narrated two-case video; cover roster and venue playback still need checking
- **Sat 17 Oct**: Internal submission target for deck, prototype and video; the [official deadline](https://www.hack4sdg.com/2026-roadmap/final-submission-2026/) is **Sun 18 Oct, 23:59 HKT**
- **Sat 24 Oct**: Final pitch, CityU Kowloon Tong

> **Current evidence boundary:** Aberdeen's saved P0/P2 tie means no plan is
> recommended. Tuen Mun's frozen 11% P2 ranks first under the team's shared
> rule, with about 4% less **modelled** E delay than P0. Simulation permits this
> labelled candidate comparison, not a measured road-saving claim. Keep the
> too-fast, early-clearing queue limitation adjacent to the result. The
> [two-case handoff](../docs/2026-10-15-two-case-demo-handoff.md) has the exact
> caption and source paths. The Q&A has current Lead source copy but still
> needs Impact review. Use the delivered v17 video and narration for the pitch.
