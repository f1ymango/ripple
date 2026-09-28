# 04 — Timeline, roles and critical path

Team: 3 × Year 2 CSE, 1 × Year 2 PHYS, 1 × Year 1 DDP (CSE + QFin).
Everyone is taking courses. Budget **6–8 hours per person per week**; weeks 2
and 3 are the heavy ones.

---

## 1. Roles

| Person | Role | Owns |
|---|---|---|
| **[you]** CSE Y2 | Lead + GenAI pipeline | scope, integration, components **B, D, F** |
| CSE Y2 #2 | Data + experiments | components **A, E** — loaders, scenario runner |
| CSE Y2 #3 | Visuals + video | component **G** + the demo video |
| PHYS Y2 | Simulation + validation | component **C** + calibration + sensitivity |
| CSE/QFin Y1 | Impact + business + pitch | component **H** + interim report + deck |

**Why this split:**
- The physicist owns *validation*, which answers the hardest Q&A question ("how
  do you know your simulation is right?"). Calibrating a model against
  measurements and quoting an error bar is a physics reflex.
- The Y1 gets well-bounded, non-code-critical work that still carries **60% of
  the judging score** (problem framing + feasibility/impact + ethics).
- Only one person integrates, so the repo does not fork.

**One decision owner per area.** If two people disagree inside someone's area,
that area's owner decides and moves on. Escalate to the lead only if it changes
scope.

---

## 2. Timeline

### Week 1 — 21–27 Sep · Setup and pick the incident
| Who | Task | Done when |
|---|---|---|
| Lead | Freeze scope; write `CLAUDE.md`; create repo; test the Incident Reader on 20 real messages | repo exists, 20 messages parsed |
| Data | Pull Aberdeen detector + incident archives; shortlist 3–5 corridor incidents with good detector coverage | shortlist in `data/candidates.md` |
| Visuals | Map that plots corridor detectors coloured by speed from a static file | screenshot posted |
| Sim | Install SUMO; build Aberdeen network from OSM; get vehicles moving | a video of cars moving |
| Impact | Gather problem evidence; line up 2–3 user interviews | `05-pitch.md` evidence section filled |

**🔒 End of week: team picks THE demo incident.** One incident, agreed by all.

### Week 2 — 28 Sep–4 Oct · Baseline and interim report
| Who | Task |
|---|---|
| Sim + Data | Fit demand to detector counts; run the incident with no intervention; produce the **validation chart** (sim vs observed) |
| Lead | Incident Reader reliable; label ~100 messages; report accuracy |
| Visuals | First timeline playback of the simulated incident |
| Impact | Draft the interim report (everyone writes one paragraph); run the interviews |

**📤 Submit interim report Sat 3 Oct** (deadline is Sun 4 Oct).

### 🚦 Go / no-go — Sun 4 Oct
> If the baseline does **not** roughly match what the detectors recorded, switch
> to the simplified ~15-link network (`03-architecture.md` §5) **that day**.
> Do not spend week 3 fixing the twin. Losing the twin is survivable; losing
> week 3 is not.

### Week 3 — 5–11 Oct · Plans and results
| Who | Task |
|---|---|
| Lead | Plan Generator producing valid `plan.json`; Briefing Writer producing briefing + VMS text |
| Data | Scenario runner for P0/P1/P2; parameter search over diversion shares |
| Sim | Sensitivity runs: compliance 30/50/70 × clearance 30/60/90; write the validation slide |
| Visuals | Three-column plan comparison + headline-numbers panel |
| Impact | Convert results into delay / cost / CO₂ figures; draft business model and ethics slides |
| *(Optional)* | WorkBuddy Award report — assign to one person **this week**, not week 4 |

### Week 4 — 12–18 Oct · Freeze, video, deck
| Date | What |
|---|---|
| Mon 12 Oct | **Everyone** attends the pitching workshop (HKU Innovation Wing 2, 14:00–17:30) |
| **Wed 14 Oct** | **🔒 RESULTS FREEZE.** No new features after this — bug fixes only. Every number in the deck is locked. |
| Wed–Fri | Visuals + Lead record and edit the ~90-second video. Impact finishes the deck; Sim writes the validation slide. |
| **Sat 17 Oct** | **📤 Submit** (deadline Sun 18 Oct) |

### Week 5 — 19–24 Oct · Rehearse
- Impact + Lead write and rehearse the 5-minute pitch.
- Everyone drills Q&A; **each person owns the questions on their own area**.
- Finalists announced Thu 22 Oct. Final Sat 24 Oct, CityU Kowloon Tong.

---

## 3. Critical path

```
demo incident chosen  →  baseline matches reality  →  three plans compared  →  video
```

If anything slips, **cut features, protect this chain.** Everything else —
what-if box, live segment, second incident, prettier map — is optional.

## 4. Cadence

- One 20-minute sync a week: **Wednesday afternoon** — the only slot everyone
  is free. Anything that cannot wait for it goes to the team chat async, with a
  stated deadline for objections, rather than pulling people into a meeting.
- Format: what I finished / what I'm on / what's blocking me. No status essays.
- Anything that changes a contract in `03-architecture.md` gets said out loud
  and the file updated the same day.
- If you have midterms in mid-October, say so **now** and shift your share into
  week 2.

## 5. Definition of done for the whole project

- [ ] One real archived incident replayed end to end
- [ ] Validation chart: simulated vs observed, with a stated error
- [ ] Three plans compared on ≥ 4 metrics
- [ ] Sensitivity: plan still wins across compliance and clearance ranges
- [ ] Incident Reader accuracy measured on ~100 labelled messages
- [ ] One on-screen moment where a real bilingual message goes in and a ranked
      plan + briefing + sign text come out
- [ ] Operator console with an Approve action and an audit log
- [ ] 2–3 user interviews recorded in `evidence/interviews/`
- [ ] ~90-second video
- [ ] Deck covering all five criteria
- [ ] Every number traceable to a file in `results/`
