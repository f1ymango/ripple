# 05 — Pitch: narrative, evidence, Q&A, ethics, business model

Five minutes, then 5–7 minutes of Q&A. The deck is preloaded by the organisers.

> **Working script, 6 Oct:** The no-closure count check is reproducible, but
> there is no accepted incident P0 or comparable P0/P1/P2 result set. Demo,
> benefit and sensitivity lines below are targets until linked to validated
> outputs in `results/`. Remove any unsupported claim at the 9 Oct checkpoint.

---

## 1. Problem statement (working draft)

> When a crash blocks a key road, Hong Kong's response relies on pre-set plans,
> and everyone gets the same advice: take the alternative route. Navigation apps
> then optimise each driver separately. Because roads behave like a circuit,
> thousands of individually sensible choices can move the jam instead of
> clearing it — delaying ambulances, deliveries and airport trips. Our goal is
> to turn an incident report into a tested, coordinated response in minutes,
> using Hong Kong's open data. The incident benefit must still be demonstrated.

## 2. Five-minute structure

| Time | Beat | Content |
|---|---|---|
| 0:00–0:40 | **The story** | 29 Jul 2026, Tsing Yi: an overturned lorry, tunnels to the airport shut intermittently, ~4 km of queues, and one instruction for everybody — "consider alternative routes, including Tsuen Wan Road." |
| 0:40–1:20 | **Why it's structural** | Wardrop: best-for-me ≠ best-for-us. Circuit analogy. Historical US estimates attribute about a quarter of all congestion to incidents; roughly 20% of incidents are secondary. These are context, not Hong Kong measurements. |
| 1:20–1:50 | **The honest gap** | HK already coordinates (ETCC, TIMS, adaptive signals). What's missing: advice is one-size-fits-all, and the systems that do this properly overseas cost USD 4–75M and took ~5 years. TD is starting a study on an AI Traffic Management Platform now — **Aberdeen first**. |
| 1:50–3:30 | **Demo** | Target sequence: real message in → parsed → forecast → three plans compared → briefing and bilingual sign text out → operator approves. Show only stages actually evidenced by 9 Oct; observed playback is available now. |
| 3:30–4:15 | **Proof** | Show the no-closure count check with its imposed-speed caveat. Add an incident-validation chart, plan benefit and sensitivity range only if comparable results exist in `results/`; otherwise state that these are not measured yet. |
| 4:15–5:00 | **Impact, ethics, next** | Who benefits, what it costs to run, what we refuse to do, the roadmap. |

**Open with the story, not the architecture.** Judges are a mixed panel —
academics, industry, NGOs, investors — not traffic engineers.

## 3. Evidence, with sources

Use these verbatim. Do not paraphrase numbers upward.

**Scale of the problem**
- Hong Kong, 2023: **17,189 road traffic accidents**, 22,269 casualties and
  28,808 vehicles involved. ([C&SD, *Road Traffic Accident Statistics in Hong Kong, 2014 to 2023*, February 2025](https://www.censtatd.gov.hk/en/data/stat_report/product/FA100071/att/B72502FA2025XXXXB0100.pdf); checked 2026-09-28.)
- TD's December 2024 digest lists **18,355 injury accidents** and **23,659 casualties**
  for 2024; these figures are marked provisional in that digest.
  ([TD, *Monthly Traffic and Transport Digest*, December 2024](https://www.td.gov.hk/filemanager/en/content_5278/2412_e.pdf); checked 2026-09-28.)

**Why incidents specifically**
- Historical FHWA estimates for the **US**, not Hong Kong: incidents account for
  **about 25% of all congestion** ([FHWA, *Reducing Non-Recurring Congestion*](https://ops-dr.fhwa.dot.gov/program_areas/reduce-non-cong.htm));
  non-recurring events including incidents, weather, construction and special
  events account for **nearly 60% of congestion delay**, and **about 20% of
  incidents are secondary incidents** ([FHWA, *Traffic Incident Management*, 2004](https://rosap.ntl.bts.gov/view/dot/66034)).

**Why coordination beats individual routing**
- Çolak, Lima & González, *Nature Communications* 7:10793 (2016): with mobile [Checked: https://www.nature.com/articles/ncomms10793, 2026-09-25]
  phone traces across five cities, **moderate levels of social-good awareness in
  routing are enough to achieve significant collective travel-time savings.**
  In their example city, user equilibrium cost 3.75 min/driver against 3.5 min
  at system optimum.
- Wardrop (1952) — user equilibrium vs system optimum. Braess's paradox (1968). [Checked: https://doi.org/10.1090/qam/41982, 2026-09-25]

**That coordinated incident response works, and what it costs**
- US Integrated Corridor Management, pre-deployment analysis: **Dallas US-75** — [Checked: https://its.dot.gov/icm/, 2026-09-25]
  740,000 person-hours saved per year, 20:1 benefit–cost, USD 14M over 10 years.
  **San Diego I-15** — 246,000 person-hours, 10:1, USD 12M. Projected BCRs
  across sites: **10:1 to 25:1**.
- **Dallas North Tollway** dynamic traffic assignment study: average network [Checked: https://its.dot.gov/icm/, 2026-09-25]
  travel time fell **9%** when response plans retimed **30 intersections**, but
  only **3%** when signal changes were limited to frontage roads. *More spatial
  coverage of the plan → more benefit.* Assumed diversion rates: **10–70%**.
- Timeline reality check: those corridors went from concept of operations in [Checked: https://its.dot.gov/icm/, 2026-09-25]
  2008 to launch in **spring 2013**.

**Hong Kong's direction of travel (why now)**
- Transport Strategy Blueprint, **February 2026**. [Checked: https://www.td.gov.hk, 2026-09-25]
- LegCo written reply, **22 Apr 2026**: TD proposes to **commence a study on the [Checked: https://www.info.gov.hk/gia/general/202604/22.htm, 2026-09-25]
  Traffic Management Platform within this year**, which will "use big data
  analytics and AI technologies to predict changes in traffic conditions,
  identify traffic bottlenecks, **develop emergency response plans**, assist
  with traffic management … and disseminate relevant information to the public",
  and will be "capable of analysing road congestion and **recommending solutions
  in real-time**". **"areas around Aberdeen identified as the first site to be
  prepared within this year."**
- Ting Kau Bridge Smart Motorway Pilot (Dec 2024) already uses AI automatic [Checked: https://www.td.gov.hk, 2026-09-25]
  incident detection; being extended to more roads.
- TD's real-time adaptive traffic signal system is being extended to about **50 [Checked: https://www.td.gov.hk, 2026-09-25]
  signalised junctions**, installation in phases from 2026.

**Prior art we must acknowledge (do not pretend to be first)**
- LLM + traffic simulator work already exists: TrafficGPT, ChatSUMO, Open-TI, [Checked: https://github.com/topics/traffic-simulation, 2026-09-25]
  SUMO-MCP, AgentSUMO. **Our novelty is the application**, not the pattern: real
  Hong Kong incident feeds → a corridor twin with explicit validation gates →
  candidate coordinated, bilingual, operator-approved responses. Incident
  replay and plan benefits remain to be established.
- DTSUMO (J. Intelligent Transportation Systems, 2025) is a published Python ⚠️ FLAG: Paper publication year marked 2025; verify exact package release version in PyPI before code integration. [Checked: https://www.tandfonline.com/toc/gits20/current, 2026-09-25]
  package that updates a SUMO twin from real-time detector data — check it
  before writing our own.

## 4. Q&A traps — and the answers

**"Isn't the Transport Department already building this?"**
> Yes — and that's the point. Their platform is at *study* stage, announced in
> April, with Aberdeen as the first pilot area. We've built the incident reader,
> plan/briefing guardrails and operator workflow on open data. The incident
> evaluator and benefit proof are not complete yet. We're not competing with
> TD; we're testing what one piece could look like.

**"How do you know your simulation is right?"**
> We don't compare simulation to reality and call the difference a benefit.
> The intended test separates observed reality, a no-intervention P0 replay
> and candidate plans. The independently reproduced no-closure count check is
> limited: speeds were imposed and incident queues and recovery are not yet
> validated. We will claim a plan benefit only after an accepted P0 and
> comparable provenance-bound plan results exist.

**"Why would drivers take a slower route?"**
> Most don't have to. Our levers are signals, road signs, fleet dispatch and
> destination-specific advice — not compulsion. The planned sensitivity test
> covers 30%, 50% and 70% compliance, but no Ripple plan benefit has been
> established at any of those levels. US corridor studies assumed 10–70%
> diversion; that is context, not a measured local compliance rate.

**"What if the language model hallucinates?"**
> It never produces a number. It reads the message, proposes candidate plans and
> writes the explanation. The simulator computes every outcome, a validator
> rejects plans that break our constraints before they're even simulated, and a
> human approves before anything is published. We also measure the Reader on
> 100 hand-labelled real messages: the initial held-out all-fields-correct
> result was 50% citywide and 75% on the corridor. After prompt and label
> corrections informed by that evaluation, the development result was 75% and
> 85%; it is not a fresh held-out score.
>
> On repeatability: the simulator is seeded, so its numbers repeat exactly. The
> model runs locally, and local inference is not bit-identical across different
> hardware — we checked on two machines, and every scored field came back the
> same while the model's own free-text note varied. The hand-written labels are
> the ground truth, so the accuracy figure does not move with the machine.

**"This only works where there are detectors."**
> Correct, and we say so on the ethics slide. The current handoff must have
> reviewed demand, routes and sources, and the result gates reject an
> unvalidated baseline. A per-corridor coverage threshold remains a proposed
> deployment policy, not a measured or implemented confidence score.

**"Isn't this just Google Maps?"**
> Google Maps is the user-equilibrium machine — it optimises for you, alone.
> We are testing network-level response plans for the person who controls signs
> and signals. Different customer, different objective; a measured benefit
> still requires an accepted incident comparison.

**"What's genuinely new?"**
> Not LLM-plus-simulator; that exists. What's new is the end-to-end path from
> Hong Kong's own bilingual incident feed, through a corridor twin checked
> against Hong Kong detector counts for a no-closure hour, to candidate
> coordinated plans with an operator in the loop. Incident validation and
> one-corridor cost are still to be demonstrated.

**"Who would pay for it?"** → §6.

**"What would you do with more time?"** → §7.

## 5. Ethics slide

- **Distributional fairness.** A plan that helps the average can hurt a
  neighbourhood. The plan validator rejects routes that exceed its residential
  exposure limit or pass schools at school-run times. The **share of delay
  pushed onto residential streets** still needs comparable evaluator results
  before it can be reported.
- **Human in the loop.** We recommend; we never actuate. Every recommendation
  and approval is written to an audit log.
- **Privacy.** Only aggregate open data — detector counts and public incident
  notices. No personal data, no vehicle identifiers, no individual tracking.
- **Coverage bias, named.** Detector density is uneven; a naive rollout would
  serve well-instrumented corridors first. A per-corridor confidence policy
  and refusal threshold are future deployment work, not current evidence.
- **Not an enforcement tool.** The government has said its platform is for
  planning and management, with automated enforcement out of scope at study
  stage. Ours is the same, by design.
- **Empowerment, not dependency.** Operators get options with reasons and
  trade-offs, not a black-box instruction. They can reject or edit any plan, and
  the briefing always states what we are unsure about.

## 6. Feasibility and business model

**Who the customer is:** the traffic operator — TD first, then tunnel and
highway operators, then large fleets.

- **Stage 1 — public sector module.** A component for TD's Traffic Management
  Platform, funded via the **Smart Traffic Fund**, which supports AI transport
  applications. The Aberdeen pilot is already scheduled; we are additive, not
  competing.
- **Stage 2 — fleets and operators.** Logistics firms, franchised bus
  operators, tunnel management companies. They already lose money to incident
  delay and control their own dispatch, so they can act on the output without
  any government integration. Subscription per corridor.
- **Stage 3 — Greater Bay Area.** The same open feed already covers the
  Shenzhen Bay Bridge and the Hong Kong–Zhuhai–Macao Bridge Link Road. The
  method transfers wherever there are detectors and an incident feed.

**The prototype uses open data and open-source simulation and does not require
us to install new sensors.** Deployment cost is not yet measured: it needs a
priced compute configuration, usage, storage and maintenance assumptions.
That boundary matters when contrasting a prototype with the cited cost of a
full ICM programme or conventional infrastructure.

**Impact metrics we would track in deployment:** vehicle-hours of delay avoided
per incident · reduction in secondary incidents · emergency-vehicle travel time
during incidents · CO₂ avoided from idling · % of incidents with a plan issued
within 10 minutes.

## 7. Roadmap (the "what next" slide)

| Horizon | Step |
|---|---|
| Now | One corridor, archived observed replay, recorded Reader evidence and a labelled fixture workflow; no accepted live incident-injection claim |
| 3 months | All Aberdeen-district incidents; automatic nightly backtest against every archived incident |
| 6 months | Second corridor (Tsing Yi / airport — the 29 Jul case, needs sensor coverage); camera-based verification |
| 12 months | Integration pilot with an operator; real sign and app delivery; measured before/after |

## 8. Slide checklist against the five criteria

- [ ] **Problem (20%)** — story, evidence with sources, stakeholders, what exists
      today and why it falls short, why now
- [ ] **Prototype (20%)** — video, what works vs simulated, realistic test case
      (a real archived incident), user testing (the interviews)
- [ ] **GenAI (20%)** — three named jobs, why GenAI beats rules, model named,
      guardrails, measured accuracy, efficiency
- [ ] **Feasibility & impact (20%)** — customer, funding path, adoption, metrics,
      scale, challenges, timeline
- [ ] **Sustainability & ethics (20%)** — fairness, human in the loop, privacy,
      coverage bias, financial sustainability, empowerment
