# Demo incident shortlist

## Decision — 28 Sep 2026

The Lead selected `IN-26-03365` as the primary demo incident and
`IN-26-06391` as backup, using Data's five-candidate review below. The backup
is reserved for a source-evidence or incident-location problem specific to the
primary; a calibration failure follows the simplified-network go/no-go on 4 Oct
in `docs/04-plan.md`.

Keep three times separate for the primary: detectors show disruption by 08:55,
TD's NEW message is timestamped 09:01, and TD reported all lanes closed at 09:36 (cleared
10:02). The first message's lane is `unspecified`; the Evaluator chooses and
discloses its physical lane assumption. Zero detector flow does not itself
prove when every lane physically closed. An operator-facing plan cannot use a
message before its publication time.

Simulation must review the affected edge, direction, detector placement, and
pre-incident fit before making a baseline-validation claim. This decision
selects the real event; it does not declare the current twin validated.

Data prepared this screening on 26 Sep 2026 from the evidence table in [`candidates.md`](candidates.md) (every corridor traffic
accident 22 Mar – 21 Sep 2026, all three Special Traffic News files) and a
bin-by-bin read of the detectors around each one. Hand-written: edit freely,
but regenerate `candidates.md` rather than editing it.

## What a demo incident has to do

**Showcase the whole loop on one real event.** The operator console receives
a real TD message, the Incident Reader turns it into `incident.json`, the Plan
Generator proposes diversions, the twin replays the morning with and without
each plan, and the briefing explains the pick. So the incident needs:

1. **A message that exercises the Reader** — ideally more than one kind across
   the set: a named lane, an unspecified closure, an escalation, a full closure.
2. **A real diversion question** — somewhere for traffic to go (Pok Fu Lam Road,
   Nam Fung Road / Wong Nai Chung Gap Road, the South Island Line), so plans
   genuinely differ.
3. **An impact the twin can be validated against** — a queue the corridor
   detectors actually saw, on ordinary days they did not.

**Be doable in three weeks.**

4. **A complete, trustworthy timeline** — TD's NEW and clearance both archived
   (three language files cross-checked).
5. **Inside the network we model**, with detectors either side of the closure.
6. **Nothing else going on** — no other corridor incident in the detector
   window, so the whole slowdown is this incident's.
7. **Fits a two-hour simulation** with a pre-incident calibration hour.

## The five

| # | Incident | When | TD's wording | What it shows | Score in `candidates.md` |
|---|---|---|---|---|---|
| ⭐ 1 | `IN-26-03365` | Fri 15 May, 09:01–10:02 | part of the lanes → **all lanes** (09:36) | the headline demo: vague message, escalation, full closure in the morning peak | 4.38 (#1 of 35) |
| 2 | `IN-26-06391` | Tue 1 Sep, 12:41–13:07 | **tunnel tube slow lane**, "only the fast lane is available" | a named lane in the corridor's bottleneck, the tunnel | 2.82 (#7)¹ |
| 3 | `IN-26-02105` | Mon 23 Mar, 08:23–09:11 | **slow lane** of the WCH Road flyover | a small, local queue: the twin's precision on a partial closure | 2.55 (#10) |
| 4 | `IN-26-03744` | Fri 29 May, 13:05–13:37 | **fast lane** of the WNC Gap Flyover | the Wan Chai end of the corridor, the other direction | 2.86 (#5)² |
| 5 | `IN-26-05951` | Tue 18 Aug, 02:53–03:56 | part of the lanes → **all lanes of the tunnel** | forced diversion; our plan against TD's own advice | 3.34 (#3) |

Four state the closed lane; `IN-26-03365` is the unspecified case (its first
35 minutes). The score only orders the evidence table: ¹ and ² are explained
below, where the score's automatic flags point at detectors that are not the
incident's.

---

### ⭐ 1. IN-26-03365 — the headline demo

**What happened.** An accident on the Wong Chuk Hang Road flyover towards the
Aberdeen Tunnel, near Yip Kan Street. TD at 09:01: *"part of the lanes ... is
closed"*. At 09:36: *"all lanes ... are closed"*. Re-opened 10:02.

**What the detectors saw** (5-minute bins against the same Friday 1 and 2 weeks
earlier, 63–81 km/h throughout):

- AID01104, at the flyover: 7 km/h at 08:55, then **no vehicles in 8 of the 9
  five-minute bins from 09:15 to 09:55** (every lane reporting; one vehicle at
  09:30) — the road was shut about 20 minutes before TD said "all lanes".
- The queue grew backwards: AID01103 from 09:05, AID01102 from 09:15, AID01101
  on Aberdeen Praya Road from 09:45 (8–43 km/h).
- Recovery front 10:05–10:20, detector by detector.
- 5 detectors credited, none on the noise floor; no other corridor incident.

**What it showcases.**

- *Reader*: the hardest real case — `lanes_closed: ["unspecified"]` first, then
  `["all"]` on the update. The Evaluator has to decide what to simulate for
  "unspecified" (the open decision in the README), and the escalation shows the
  plan being revised.
- *Plans*: a full closure of the only road to the tunnel at 9 am — every
  diversion option matters (Nam Fung Road to Wong Nai Chung Gap Road, Pok Fu
  Lam Road, the South Island Line), and doing nothing is visibly costly.
- *Twin and validation*: four detectors in a row record the queue's growth and
  the recovery. That's a strong, visual "simulated vs observed" chart.
- *Console*: the map turns red detector by detector back to Aberdeen Praya Road.

**Doable.** 38% archive coverage, 600 of 896 slots with both count and speed.
Weekday, no other incident, timeline complete in all three language files.

**Watch out for.** Direction-aware map matching now selects a northeast edge
for AID01104, but the OSM network is still a draft and the tunnel detector
AID01217 has no nearby edge that passes the direction check. Hand-review the
edge and position mappings before validating this incident.

### 2. IN-26-06391 — a named lane in the tunnel

**What happened.** An accident in the Aberdeen Tunnel towards Wan Chai: *"the
tunnel tube slow lane ... is closed to all traffic. Only the fast lane is
available"*. 12:41–13:07.

**What the detectors saw.** AID01107 in the tunnel went from about 53 km/h to
**no vehicles at 12:35**, then 5–13 km/h until 13:15 (ordinary days 57–68).
Upstream AID01106 also no vehicles at 12:40, then 2–14 km/h; AID01105 fell
from ~90 to 2–22 km/h. **Downstream**, AID01108 was starved: 30–390 veh/h
against ~1,000. Recovery 13:10–13:20.
Six detectors credited, the tunnel's AID01107 strongest (37 km/h below
ordinary for 45 minutes).
¹ The table flags an early onset (−31 min); that comes from AID01215 and
AID01110 on Canal Road slowing at 12:10–12:15, not from the tunnel, whose
detectors dropped 6 minutes before TD's report.

**What it showcases.** The cleanest possible Reader case (lane named, lane
left named) on the corridor's bottleneck. The twin has to reproduce a
one-lane tunnel choke: queue upstream, starvation downstream. It's a good
second validation incident on different detectors from #1.

**Doable.** Weekday midday, 26 minutes, no other incident; 499 of 700 slots
with both count and speed.

### 3. IN-26-02105 — a small, local queue

**What happened.** The slow lane of the Wong Chuk Hang Road flyover towards
Aberdeen, near Yip Hing Street, 08:23–09:11 on a Monday.

**What the detectors saw.** AID01219, just before the flyover, fell from ~70
to 16–46 km/h from 08:10 to 09:05 and recovered at 09:10, one minute before
TD's clearance. The detectors either side (AID01218, AID01220) stayed normal.

**What it showcases.** Not every incident is a disaster. A one-lane closure
with a local queue tests whether the twin — and our plans — are proportionate:
the right recommendation may be "no diversion, warn drivers". Also the
opposite direction to #1 (Aberdeen bound).

**Doable.** 618 of 868 slots with both; onset 13 minutes before the report.

### 4. IN-26-03744 — the Wan Chai end

**What happened.** The fast lane of the Wong Nai Chung Gap Flyover towards the
Aberdeen Tunnel, near Queen Elizabeth Stadium, 13:05–13:37.

**What the detectors saw.** AID01215 on Canal Road Flyover (upstream) fell to
17–21 km/h at 13:20–13:30 against 59–72; AID01216 on the flyover ran 53–58
against ~80, then 15–27 km/h at 13:35–13:45 as the queue cleared through.
² The table's "strongest" detector is AID01108, northbound — the opposite
direction, slow from 12:35; it is not this incident, and it is where the
table's early-onset flag comes from.

**What it showcases.** The northern end of the corridor and the tunnel-bound
direction from Wan Chai, so the demo is not all Aberdeen side. A named fast
lane (`lanes_closed: ["fast"]`).

**Doable.** Short (32 min) but clean; ordinary days 3 and 4 weeks earlier (the
nearer ones had incidents).

### 5. IN-26-05951 — the whole tunnel closed

**What happened.** At 02:53 TD reported part of the lanes of Wong Chuk Hang
Road closed and, the same minute, **all lanes of the Aberdeen Tunnel towards
Wan Chai**. Night buses N72, N90, N170 and N171 were diverted; TD advised
motorists to use Nam Fung Road. Re-opened 03:56.

**What the detectors saw.** AID01107 in the tunnel carried **no vehicles for
55 minutes** from 02:25 (every lane reporting; 90–360 veh/h on ordinary nights);
AID01106 upstream none for 20 minutes. Traffic returned about 03:40.

**What it showcases.** The most severe closure there is, with TD's own advice
to compare against: does our recommended plan beat "use Nam Fung Road"? The
Reader gets the "all lanes" case.

**Doable, with a caveat.** At 3 am there is little traffic, so delays are
small — keep it as the contrast case, not the headline.

---

## Backups, and why they are not in the five

- `IN-26-03212` (Sat 9 May, part of the lanes, very strong signal) — another
  corridor accident, IN-26-03214, starts 10:31 in the same window.
- `IN-26-03030` (#2 in the table) — on Shek Pai Wan Road, which *is* the
  western alternative; good evidence, but it cannot show diverting onto it.
- `IN-26-05992`, `IN-26-06874` — the slowdown began 31–34 minutes before TD's
  report, so part of it may be something else.
- `IN-26-02923` (slip road to Ap Lei Chau) — weak on re-check (13 km/h below
  ordinary) and needs the slip road modelled.

## Replaying them

Each window is the pre-incident hour (for calibration, GEH in the pre-incident
hour per `docs/03-architecture.md` §4), the incident, and the recovery.
`twin-detectors` writes one observation per 5-minute slot from the window's
start, which is the simulation's time 0.

| Incident | Time 0 | End | Queue seen | TD NEW | Clearance | Command |
|---|---|---|---|---|---|---|
| IN-26-03365 | 07:55 | 10:35 | 08:55 (3600 s); no vehicles 09:15 (4800 s) | 09:01 (3960 s) | 10:02 (7620 s) | `python -m src.loaders.fetch twin-detectors --start 2026-05-15T07:55 --end 2026-05-15T10:35` |
| IN-26-06391 | 11:35 | 13:40 | 12:35 (3600 s) | 12:41 (3960 s) | 13:07 (5520 s) | `... --start 2026-09-01T11:35 --end 2026-09-01T13:40` |
| IN-26-02105 | 07:10 | 09:45 | 08:10 (3600 s) | 08:23 (4380 s) | 09:11 (7260 s) | `... --start 2026-03-23T07:10 --end 2026-03-23T09:45` |
| IN-26-03744 | 11:55 | 14:10 | 12:55 (3600 s) | 13:05 (4200 s) | 13:37 (6120 s) | `... --start 2026-05-29T11:55 --end 2026-05-29T14:10` |
| IN-26-05951 | 01:25 | 04:30 | 02:25 (3600 s) | 02:53 (5280 s) | 03:56 (9060 s) | `... --start 2026-08-18T01:25 --end 2026-08-18T04:30` |

Inject the closure when the detectors saw the queue, not at TD's NEW:
TD reports 6–28 minutes after traffic is already affected. The windows run
past the twin template's 7200 s end, so set `end` to match.
