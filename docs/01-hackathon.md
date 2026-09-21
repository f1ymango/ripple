# 01 — Hackathon rules, dates and judging

Source: hack4sdg.com (checked 21 Sep 2026). Organised by an alliance of Hong
Kong's eight publicly funded universities, powered by HKU Common Core.
Official technical partner: Tencent Cloud (WorkBuddy).

---

## 1. Dates that bind us

| Date | Day | What |
|---|---|---|
| 19 Sep 2026 | Sat | Launch day, HKU Centennial Campus (done) |
| 9 Oct 2026 | Fri | Visit to Sino Inno Lab (optional) |
| **4 Oct 2026** | **Sun** | **Interim report due** — online progress report clarifying the social problem and the preliminary idea. Team members may be added/removed/replaced on or before this date. |
| 12 Oct 2026 | Mon | Pitching workshop + networking mixer, HKU Innovation Wing 2 (14:00–17:30) |
| **18 Oct 2026** | **Sun** | **Pitch deck AND prototype information due** (demos/apps, videos, technical links or files). Deck may include appendices. Last date to change thematic track. |
| 22 Oct 2026 | Thu | Finalists announced |
| **24 Oct 2026** | **Sat** | **Final demo / pitch day**, CityU Hong Kong, Kowloon Tong. 09:00–18:00 |

**Our internal deadlines:** results freeze **Wed 14 Oct**; submit **Sat 17 Oct**
(one day early). Do not plan to the real deadline.

Selection: teams are vetted on interim report + pitch deck quality, against the
judging criteria. **Only 10 teams per track reach the final (40 total).**

Final format: **5 minutes to pitch, then 5–7 minutes of Q&A.** The organisers
preload the submitted deck.

## 2. Judging criteria — five criteria, 20% each

### Convincing framing of problem (20%)
Is the specific issue and pain point clearly defined, with evidence? Who are the
stakeholders? **What existing solutions have been attempted and why have they
been ineffective?** Does it address root causes rather than symptoms? Why now?

> For us: name TD's existing systems honestly, then name the precise gap.
> See `00-brief.md` §2 and `05-pitch.md`.

### Prototype / demo (20%)
Functional prototype or demo showing the solution in action. **"How complete is
the prototype (what works vs. what's simulated)?" "Can the prototype handle
realistic test cases?" "Has the prototype been tested with potential users?"**

> ⚠️ *"Teams without a technical prototype will be heavily penalised in both the
> Prototype/demo and Appropriate technical component criteria."* — that is 40%.
> For us: label what is simulated, replay a **real** archived incident, and do
> 2–3 short user interviews so we can answer the user-testing question.

### Appropriate technical component (20%)
How specifically does the solution leverage **GenAI**? Why is GenAI particularly
suited here? Which models/techniques? How does it improve on non-AI
alternatives? What are the limitations and how are they addressed? How
efficiently does it use compute?

> For us: three named GenAI jobs (Incident Reader, Plan Generator, Briefing
> Writer), each with a reason a non-AI approach fails, plus the explicit
> guardrail that **the LLM never produces the numbers**.

### Feasibility and impact (20%)
Business model or plan? Practically implementable under real-world constraints?
How do users access and adopt it? What metrics measure impact? Scale of impact?
Implementation challenges? Realistic deployment timeline?

### Sustainability and ethics (20%)
Long-term sustainability, financial sustainability, scalability and integration
with existing systems, ethical concerns (bias, privacy, accessibility,
unintended consequences), community feedback, and whether the solution empowers
users rather than creating dependency.

## 3. Rules we must not break

- Team of **3–5 students**, at least 50% undergraduate. (6th member possible by
  special permission for interdisciplinary/mixed-university teams.) — We are 5.
- Participants may use **any** AI language, tool or framework, provided licences
  and terms are respected. But the team **must demonstrate how GenAI is used**
  and **must build a working technical prototype**.
- Entry must be at **preliminary stage** — not already incubated or seed-funded.
- Our final submission **must not be the same solution or prototype previously
  submitted to another competition or an assessment**. (It may be entered
  elsewhere *afterwards*.)
- **Plagiarism results in disqualification.** Attribute open-source components,
  datasets and any code we did not write.
- Each team competes in **one** track.

## 4. Prizes and what follows

- Per track: **Gold HK$5,000 · Silver HK$3,000 · Bronze HK$2,000.** 12 prizes,
  HK$40,000 total. Split evenly among team members, paid by each member's own
  university.
- **Gold and Silver teams (8 total) are automatically admitted to the Finals of
  Techathon+**, organised by HKSTP. Non-winners may still apply.
- All participating teams can apply for seed programmes through their own
  universities — up to HK$100,000 funding plus HKSTP incubation. **Mixed-university
  teams are explicitly advantaged here** — we qualify.

## 5. Best WorkBuddy Award (optional, separate)

Tencent Cloud's separate prize for the most thoughtful, effective and
responsible use of **WorkBuddy**, their agentic AI platform (free tokens were
given to participants at launch day).

- Requires a **separate WorkBuddy Award Report** submitted *with* the final
  pitch deck and prototype. Report details were released on launch day — check
  the launch-day materials.
- **Does not affect the main prizes.**
- Criteria: Purposeful Human-AI Collaboration 30% · Reusable Skills, Experts,
  Agents or Automation 25% · Quality of Outcomes 20% · Responsible Use and
  Validation 15% · Precision and Efficiency 10%.
- Judges reward **reusable** assets others can adopt, and **evidence**
  (screenshots, workflow records, before-and-after examples) over claims. More
  prompts/tokens does **not** score higher.
- Prize: Tencent talent pool + internship fast track, a visit/exchange at
  Tencent Hong Kong, social-media spotlight, certificate and gift pack.

> **Decision needed:** are we entering this? If yes, it is cheap — we are
> already keeping an AI log (`evidence/ai-log/`), and our Incident Reader
> prompt + schema is exactly the kind of "reusable asset" they reward. Assign
> it to one person in week 3, not week 4.

## 6. Track 1 scope (we are comfortably inside it)

"Green Transport & Smart Mobility — Reimagine how people and goods move across
Hong Kong and the Greater Bay Area: cleaner, smarter, more accessible."
Listed examples include **"Digital twins for traffic and congestion
simulation"** and "AI-optimised public transport routing and demand
forecasting".

## 7. What last year's winners looked like

2025 winners were, almost without exception, **tools a person visibly uses**: a
voice-based interview practice platform, a rights chatbot for migrant workers, a
real-time sign-language interpreter, an elderly medication companion, an AR
heritage app. A systems/infrastructure project can win, but the demo **must show
a human using it**. That is why component G (operator console) is not optional —
it is the thing judges will remember.
