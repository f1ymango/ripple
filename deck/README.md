# Presentation Deck & Evidence Pack

This folder holds reviewable slide copy, updated with 13 Oct GenAI evidence.
It does not yet contain a PowerPoint/PDF deck or a final video export. The
[submission manifest](submission-manifest.md) distinguishes source material,
local-only artifacts and deliverables that are still missing.

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
| Problem, pitch and evidence pack | Impact | Markdown sources are reviewable; rendered deck is not yet delivered |
| Observed incident prototype | Visuals + Lead | Merged and locally rehearsed; no route recommendation or validated plan comparison |
| Reader / GenAI evidence | Lead | Saved input, output, call log and evaluation exist; video pickup remains |
| Plan Generator | Lead | Actual 13 Oct model-generated drafts and limitations in the [GenAI handoff](../docs/lead-genai-handoff-2026-10-13.md); no accepted incident recommendation |
| Briefing Writer | Lead | Later 13 Oct model calls produced structurally valid synthetic drafts, both rejected on semantic review; no accepted new bilingual output. Offline fixture capability is separate ([follow-up](../docs/lead-genai-follow-up-2026-10-13.md)). |
| Evaluator and provenance | Data | Diagnostic implementation and integrity fixes merged through PR #61; scientific acceptance remains NO-GO |
| Simulation validation | Simulation | Joint incident review remains NO-GO for public plan ranking |
| Video | Visuals | Shot list and captions are versioned; playable export and source manifest are not delivered here |

---

## 2. File Inventory & Index

| File | Description | Status & Freeze Boundary |
| :--- | :--- | :--- |
| [slides.md](slides.md) | Slide structure aligned with 5 scoring criteria | Draft; public claims checked 11 Oct |
| [real-vs-simulated.md](real-vs-simulated.md) | Observed sources, diagnostic SUMO runs and unsupported benefit claims | Draft; evidence boundary checked 11 Oct |
| [costing.md](costing.md) | Resource questions and BCR limitations | Draft; operating cost not measured |
| [qa-sheet.md](qa-sheet.md) | Technical Q&A and known limitations | Draft; Reader score history and incident-model caveats checked 11 Oct |
| [video-shot-list.md](video-shot-list.md) | Demo video storyboard and source boundaries | Draft; final export outstanding |
| [submission-manifest.md](submission-manifest.md) | Deliverable, evidence, owner and claims inventory | Updated 13 Oct; missing exports are explicit |

---

## 3. Key Dates & Governance

- **Sat 3 Oct**: Interim report submitted
- **Thu 15 Oct**: Evidence pack, editable deck/export and accessible video checkpoint
- **Fri 16 Oct (provisional)**: **Results/claims freeze** — lock supported figures; exact hour unconfirmed (Lead update, 13 Oct)
- **Sat 17 Oct**: Internal submission target for deck, prototype and video (official deadline: 18 Oct)
- **Sat 24 Oct**: Final pitch, CityU Kowloon Tong

> **Evidence boundary, 11 Oct:** Data and Simulation retain NO-GO for public incident plan comparisons. The observed-message and detector demo can proceed; route recommendations, evaluated-vehicle animation and benefit claims remain outside the public cut. The 14 Oct freeze does not imply model sign-off. PR #53 delivered observed playback code, while the final video and deck export still need delivery.

The deadline in that historical note is superseded by the 13 Oct schedule
above. Its scientific acceptance boundary still applies.
