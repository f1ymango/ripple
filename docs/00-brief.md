# 00 — Project brief (read this first)

**Codename:** Ripple *(provisional — alternatives: Detour, Circuit, ReRoute HK)*
**Event:** Hong Kong Inter-University GenAI Hackathon for the SDGs 2026
**Track:** 1 — Green Transport & Smart Mobility
**Final submission:** 18 Oct 2026. **Final pitch:** 24 Oct 2026.

---

## 1. One-liner

> An AI incident co-pilot for traffic operators. Within minutes of an incident
> report, it forecasts how the jam will spread, tests a handful of response
> plans in a digital twin, recommends the plan with the least total delay, and
> drafts the messages that split traffic across alternatives — instead of
> sending everyone down the same detour.

## 2. The problem, stated honestly

Road networks are not "if road A is blocked, take road B". They behave like a
circuit: the capacity of one road depends on many others. The classic result is
**Wardrop (1952)** — what is best for each individual driver (user equilibrium)
is not what is best for everyone (system optimum) — and **Braess's paradox** is
the extreme case where adding capacity makes everyone slower.

That gap is real and measurable. But be careful how you claim it:

**What is NOT our gap (a judge will know this):**
- Hong Kong already responds at system level. The Transport Department's
  Emergency Traffic Co-ordination Centre has run since 2000, the Traffic and
  Incident Management System since end-2017, and signals are already retimed in
  real time during major incidents. TD keeps contingency plans for individual
  strategic routes.
- "Too hard to model" is overstated. The US Integrated Corridor Management
  programme has used simulation to pick incident responses since the 2010s.

**What IS our gap:**
1. Those overseas systems cost USD 4–75M over ten years and took ~5 years from
   concept to launch. That is not reachable for every corridor.
2. Hong Kong's public incident advice is **one-size-fits-all**. On 29 Jul 2026,
   an overturned lorry on Cheung Tsing Highway closed tunnels toward the
   airport; queues hit ~4 km and motorists were told to "consider alternative
   routes, including Tsuen Wan Road". Everyone got the same detour.
3. Navigation apps then re-optimise **each driver separately**, which is exactly
   the user-equilibrium behaviour that moves a jam instead of clearing it.
4. TD is starting a study this year on an AI Traffic Management Platform that is
   meant to predict conditions, develop emergency response plans and recommend
   measures in real time — with **Aberdeen as the first pilot area**. We build
   one working module of that, on open data, and show it works.

## 3. Scope — what we build vs what we do not

| Build for real | Simulate, and label it | Explicitly out of scope |
|---|---|---|
| Incident Reader tested on ~100 archived messages | Signal timing changes (inside SUMO only) | City-wide control |
| Aberdeen twin calibrated to detector data | Driver compliance, shown as a range | Training our own traffic model |
| 3+ plan comparison with metrics | Delivery to real signs / apps (mock screens) | A consumer navigation app |
| Operator console, briefing, messages, what-if | Camera-image verification (stretch only) | Greater Bay Area coverage |

**We recommend; we never control.** Nothing is published or actuated without a
human operator approving it. Say this out loud in the pitch — it removes most
of the ethics and safety objections before they are raised.

## 4. The eight components

### A. Data layer *(code)*
- **A1 Detector archive loader** — historical 30-second raw detector XML for a
  chosen date window → tidy table (`timestamp, detector_id, lane, speed_kmh,
  volume, occupancy_pct, valid`).
- **A2 Incident archive loader** — archived Special Traffic News snapshots,
  deduped by `INCIDENT_NUMBER`, assembled into a timeline
  (NEW → UPDATED → CLOSED) so we know **start time and clearance time**.
- **A3 Detector geo table** — locations CSV filtered to the Aberdeen corridor,
  each detector mapped to a simulation edge + position.
- **A4 Live poller** — same parsers pointed at the live URLs, for the final
  live segment of the demo.

### B. Incident Reader — **GenAI #1** *(code)*
Free-text bilingual incident message in → strict JSON out (road, direction,
landmark, lanes closed, incident type, in-scope flag, confidence).
**Why GenAI is the right tool here:** the feed is prose, in two languages,
inconsistently phrased, and its latitude/longitude fields are usually empty.
Rule-based parsing breaks; an LLM with a fixed output schema does not.
**Deliverable:** an accuracy number on ~100 hand-labelled messages.

### C. The twin *(code)*
- **C1 Network** — SUMO network for the Aberdeen corridor, built from
  OpenStreetMap and cleaned.
- **C2 Demand** — traffic fitted so simulated detector readings match observed
  readings for the pre-incident hour.
- **C3 Incident injection** — structured incident → lane closure on the correct
  edge for the correct duration.
- **C4 Baseline run** — replay with no intervention.
- **Validation** — SUMO induction loops placed at the real detector positions,
  so comparison is like-for-like. Report GEH and a speed error.

### D. Plan Generator — **GenAI #2** — plus optimiser *(code)*
- **D1** LLM drafts 3–5 candidate plans as strict JSON: diversion shares per
  origin–destination group, signal tweaks, sign-message intent, public-transport
  nudge, emergency priority corridor.
- **D2** A small parameter search tunes the diversion percentages.
- **D3** A constraint validator rejects plans that push too much traffic onto
  residential or school streets, *before* they are simulated.
- **The LLM proposes. The simulator decides.**

### E. Evaluator *(code)*
Runs every plan in the twin. Metrics: total vehicle-hours of delay, delay vs
do-nothing, maximum queue length, 95th-percentile corridor travel time,
emergency-vehicle travel time, CO₂, and share of delay borne by residential
streets. Sweeps compliance (30/50/70%) × clearance time (30/60/90 min).
**Its output table is the single source of truth for every number we present.**

### F. Briefing Writer — **GenAI #3** *(code)*
Chosen plan + metrics in → operator briefing (why this plan, what it trades
off, what to watch), character-limited bilingual variable-message-sign text,
destination-specific public messages, and an explicit uncertainty line.
A natural-language what-if question maps back to a re-run of E. This is the
agentic loop and it is what makes the demo feel alive.

### G. Operator console *(code — this is the visible product)*
Corridor map with detectors coloured by speed · incident card showing the raw
message beside the parsed structure · three-column plan comparison with metrics
and mini flow maps · 60-minute timeline scrubber · message panel with an
**Approve** button that writes an audit log · what-if box.

### H. Evidence pack *(not code)*
Validation chart, results table, parser accuracy, audit-log sample, user
interview notes. This is what wins the Q&A.

## 5. Why Aberdeen

- TD named areas around Aberdeen as the **first pilot site** for its Traffic
  Management Platform. Our pitch lands directly on their roadmap.
- The open detector feed covers the corridor in **both directions**: Aberdeen
  Praya Road → Wong Chuk Hang Road → Aberdeen Tunnel → Wong Nai Chung Gap
  Flyover → Canal Road Flyover, plus Pok Fu Lam Road and Shek Pai Wan Road on
  the western alternative. See `02-data.md` for the detector IDs.
- It is a small, bounded "circuit": one tunnel, a few low-capacity hill-road
  alternatives, and the MTR South Island Line as a mode shift.
- **Queen Mary Hospital** sits on the western alternative, which gives us a
  lives-at-stake metric (emergency travel time) that is honest and specific.
- Use the 29 Jul 2026 Cheung Tsing Highway incident as the **opening story** and
  as "the next corridor" — not as the demo. There are no detectors on Cheung
  Tsing Highway in the open feed.

## 6. How we prove it works

Three runs, not two. This is the single most important methodological point:

| Run | What it is | What it proves |
|---|---|---|
| **Reality** | What the detectors actually recorded during the incident | — |
| **Baseline sim** | Our twin replaying the incident, no intervention | The twin can be trusted (compare to Reality) |
| **Plan sim** | Same twin, our coordinated response | The improvement (compare to Baseline) |

Our headline claim is **Plan vs Baseline**. The **Reality vs Baseline** match is
our credibility. Never claim an improvement by comparing a simulation directly
against reality — a judge will correctly call that unfair.

## 7. Glossary

- **User equilibrium (UE)** — every driver picks their own fastest route.
- **System optimum (SO)** — routes chosen to minimise total travel time for
  everyone. UE ≠ SO; the gap is the opportunity.
- **Braess's paradox** — adding a road can make everyone slower under UE.
- **Non-recurring congestion** — jams caused by incidents/weather/works rather
  than by normal daily demand.
- **Secondary incident** — a crash or breakdown caused by the queue from a first
  incident.
- **GEH** — traffic-engineering statistic comparing modelled and observed flows:
  `GEH = sqrt( 2·(M−C)² / (M+C) )`. Common acceptance rule: GEH < 5 for at least
  85% of counts.
- **VMS** — variable message sign (the overhead electronic road signs).
- **STN** — Special Traffic News, TD's incident feed.
- **Twin / digital twin** — the simulation kept in step with real measurements.
