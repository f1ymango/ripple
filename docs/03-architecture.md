# 03 — Architecture and module contracts

The point of this file: **each person can build their module against a fixed
interface without waiting for anyone else.** If you change a contract here, say
so in the team chat the same day.

---

## 1. Pipeline

```
 STN message (bilingual prose)
        │
        ▼
 [B] Incident Reader  ── GenAI #1 ──►  incident.json
        │                                   │
        │                                   ▼
 detector archive ──► [A] loaders ──►  network_state.json
        │                                   │
        │                                   ▼
        └────────────────────────►  [C] Twin (SUMO)  ──► baseline result.json
                                            ▲
                                            │
 [D] Plan Generator ── GenAI #2 ──► plan.json ──► constraint validator
        │                                   │            │ (reject early)
        │                                   ▼            ▼
        └── optimiser tunes shares ──► [E] Evaluator ──► result.json (per plan)
                                            │
                                            ▼
                                 [F] Briefing Writer ── GenAI #3 ──► briefing.json
                                            │
                                            ▼
                                 [G] Operator Console  ──► approval → audit_log
```

**Hard rule:** the LLM produces `incident.json`, `plan.json` and
`briefing.json`. It never produces anything in `result.json`. Every number a
judge sees comes out of the simulator.

---

## 2. Repository layout

```
ripple/
├── CLAUDE.md                 # points at 00-brief, 02-data, 03-architecture
├── data/
│   ├── raw/                  # downloaded archives (gitignored)
│   ├── detectors.csv         # locations, filtered to corridor
│   └── labelled_incidents/   # ~100 hand-labelled STN messages (gold set)
├── src/
│   ├── loaders/              # A — detector + incident archive, live poller
│   ├── reader/               # B — GenAI #1 + schema + validator + scorer
│   ├── twin/                 # C — SUMO net, demand, incident injection
│   ├── plans/                # D — GenAI #2, constraint validator, optimiser
│   ├── evaluator/            # E — runs scenarios, extracts metrics
│   ├── briefing/             # F — GenAI #3
│   └── console/              # G — the UI
├── sim/
│   ├── aberdeen.net.xml      # SUMO network
│   ├── detectors.add.xml     # E1 induction loops at real detector positions
│   └── scenarios/
├── results/                  # ⭐ single source of truth for every number
│   ├── validation.csv
│   └── runs/<run_id>.json
├── evidence/
│   ├── ai-log/               # prompts + responses we relied on
│   ├── interviews/
│   └── audit_log.jsonl
└── deck/
```

---

## 3. Contracts

### `incident.json` — output of [B]

```json
{
  "incident_id": "IN-26-01234",
  "source_message_en": "Due to traffic accident, the fast lane of ...",
  "source_message_zh": "因交通意外，...",
  "announced_at": "2026-03-14T08:12:44+08:00",
  "closed_at": "2026-03-14T09:31:02+08:00",
  "status": "NEW",
  "district": "Southern",
  "road_name": "Aberdeen Tunnel",
  "direction": "Causeway Bay bound",
  "near_landmark": "Wong Chuk Hang Hospital",
  "between_landmark": null,
  "lat": 22.24999,
  "lon": 114.17629,
  "coords_source": "source | inferred_from_landmark | none",
  "incident_type": "traffic_accident",
  "lanes_closed": ["fast"],
  "lanes_total": 2,
  "in_scope": true,
  "confidence": 0.86,
  "notes": "lat/lon absent in source; inferred from landmark"
}
```

- `incident_type` ∈ `traffic_accident | vehicle_breakdown | road_works |
  flooding | object_on_road | public_event | public_transport_notice | other`
- `lanes_closed` ⊂ `fast | middle1 | middle2 | slow | hard_shoulder | all`

  **Middle-lane ordering — unresolved for 4-lane roads.** On a 3-lane road the
  single middle lane is `middle1`, matching the feed's plain `Middle Lane`; no
  ambiguity. On a **4-lane** road it is not established whether `middle1` is the
  lane next to `fast` or next to `slow`: the data-dictionary PDF numbers them
  Fast, Middle Lane 2, Middle Lane 1, Slow, while the XML serialises them Fast,
  Middle Lane 1, Middle Lane 2, Slow, and detector readings weakly favour the
  latter. See `02-data.md` §1 for the evidence and how to settle it.

  `src/reader/prompts/system.md` currently follows the PDF. **Leave it alone
  until the question is settled** — changing it on a guess is worse than a
  known unknown. The exposure is one detector (AID01217, Aberdeen Tunnel
  toll-plaza approach) and one function ([E]'s name→SUMO-index mapping, week 3).

  **Lane names, not indices, travel between modules.** An index is meaningless
  without a counting convention, and the same index denotes a different physical
  lane on a 2-, 3- or 4-lane road. The conversion to a SUMO lane index happens
  once, in [E], where the lane count and the left-hand-traffic convention are
  both known.

- `in_scope = false` for processions, PT notices, anything outside the corridor.
- `confidence` is the model's own; **always** shown to the operator in [G].

### `network_state.json` — output of [A], input to [C]

```json
{
  "timestamp": "2026-03-14T08:10:00+08:00",
  "window_minutes": 5,
  "detectors": [
    {"detector_id":"AID01107","lane":"fast",
     "speed_kmh":62,"volume":71,"occupancy_pct":9,"valid":true}
  ],
  "offline_count": 2
}
```

### `plan.json` — output of [D]

```json
{
  "plan_id": "P2",
  "label": "Coordinated split",
  "rationale": "Split Central-bound demand to Pok Fu Lam Rd and hold ...",
  "diversions": [
    {"od_group":"Aberdeen->Central","via":"Pok Fu Lam Road","share":0.35},
    {"od_group":"Aberdeen->Causeway Bay","via":"Wong Nai Chung Gap Road","share":0.20}
  ],
  "signals": [{"junction_id":"J12","green_extend_s":8}],
  "vms": [{"sign_id":"VMS-ABD-1","intent":"divert Central-bound to Pok Fu Lam Rd"}],
  "pt_nudge": {"mode":"MTR South Island Line","intent":"shift discretionary trips"},
  "priority_corridor": {"od":"Aberdeen->Queen Mary Hospital",
                        "keep_clear":["Pok Fu Lam Road"]},
  "constraints_checked": ["residential_share_under_15pct","no_school_street_peak"]
}
```

Three plans are mandatory in every run so the comparison is always fair:
- `P0` **Do nothing** — the counterfactual.
- `P1` **Single broadcast detour** — today's practice: one alternative, all
  traffic told the same thing.
- `P2…Pn` **Our coordinated plans.**

### Constraint validator (runs before simulation)

Rejects a plan if any is true. Tune the thresholds, but keep them explicit —
they are the ethics slide.
- residential-street share of diverted flow > 15%
- any diversion routed past a school between 07:30–08:30 or 15:00–16:00
- the emergency priority corridor receives any diversion
- diversion shares for an OD group sum to > 1.0
- a `via` road is itself blocked by the incident

### `result.json` — output of [E]

```json
{
  "run_id": "2026-03-14_ABD_P2_c50_t60",
  "plan_id": "P2",
  "incident_id": "IN-26-01234",
  "scenario": {"compliance": 0.5, "clearance_min": 60, "seed": 42},
  "metrics": {
    "total_vehicle_hours_delay": 412.8,
    "delay_vs_do_nothing_pct": -23.4,
    "max_queue_m": {"AID01107": 1450, "AID01106": 880},
    "corridor_tt_p95_min": 21.4,
    "emergency_tt_min": 9.2,
    "co2_kg": 1830,
    "residential_delay_share_pct": 12.1,
    "vehicles_completed": 18422
  },
  "validation": {"geh_under_5_pct": 88.0, "speed_mape_pct": 11.3}
}
```

`validation` is populated only for the **baseline** run (`P0` against reality).

### `briefing.json` — output of [F]

```json
{
  "run_id": "...",
  "recommended_plan_id": "P2",
  "operator_briefing_en": "…3–5 sentences: what we expect, why this plan, what it trades off, what to watch…",
  "operator_briefing_zh": "…",
  "vms_messages": [
    {"sign_id":"VMS-ABD-1","text_en":"ABERDEEN TUNNEL BLOCKED // USE POK FU LAM RD","text_zh":"香港仔隧道封閉 // 改行薄扶林道","chars_en":46}
  ],
  "public_messages": [
    {"audience":"Central-bound drivers","text_en":"…","text_zh":"…"},
    {"audience":"Causeway Bay-bound drivers","text_en":"…","text_zh":"…"},
    {"audience":"Goods vehicle fleets","text_en":"…","text_zh":"…"}
  ],
  "uncertainty_note_en": "Assumes ~50% of drivers follow advice and 60-minute clearance. If clearance runs long, expect …",
  "sources": ["results/runs/2026-03-14_ABD_P2_c50_t60.json"]
}
```

⚠️ VMS text must respect a character limit (assume **≤ 60 characters per line,
3 lines** unless we find TD's real spec). The Writer must count and the
validator must enforce it — a message that does not fit is not a message.

### `audit_log.jsonl` — written by [G]

One line per operator action: `{timestamp, incident_id, run_id, plan_id,
action: "viewed|approved|rejected|edited", operator, note}`.
This is a *product feature* (accountability) and an *ethics slide*, for free.

---

## 4. Simulation conventions (component C/E)

- **Simulator:** SUMO (Eclipse, open source), driven from Python via TraCI.
- **Network:** build from OpenStreetMap with `netconvert --osm-files`, then hand-clean
  the corridor. Check turn restrictions against TD's Road Network if anything
  looks wrong.
- **Detectors in the sim:** place `<inductionLoop>` (E1) detectors at the exact
  lat/lon of the real detectors, converted to edge+position. This makes
  validation a like-for-like comparison — simulated "detector" vs real detector,
  same place, same quantity.
- **Demand:** generate candidate routes with `randomTrips.py`, then fit flows to
  observed counts with `routeSampler.py`. (`dfrouter` is an alternative built
  specifically for detector data — try it if routeSampler fights you.)
- **Incident injection:** close lanes with a rerouter `closingLaneReroute`, or
  via TraCI by disallowing vehicle classes / setting lane speed near zero for
  the incident duration.
- **Compliance:** model as the fraction of affected vehicles that are rerouted.
  Run 30% / 50% / 70%. Published US corridor studies assumed diversion rates of
  10–70%, so our range is defensible.
- **Outputs:** `--tripinfo-output` (duration, timeLoss, waiting), `--summary-output`,
  `--queue-output`, and emissions via the emissions device for CO₂.
- **Runs are seeded and repeatable.** `run_id` encodes date, corridor, plan,
  compliance and clearance. Never hand-edit a results file.

### Validation acceptance targets (state these on the validation slide)

- **GEH < 5 for ≥ 85% of detector counts** in the pre-incident hour.
  `GEH = sqrt( 2·(M−C)² / (M+C) )`, M = modelled, C = counted.
- Speed MAPE ≤ ~15% on 5-minute bins across corridor detectors.

If we miss these, **say so and report the real number.** An honest 72% with an
explanation beats a claimed 95% a judge can poke.

---

## 5. Tech choices

| Need | Choice | Note |
|---|---|---|
| Language | Python 3.11+ | everything except the console |
| Simulation | SUMO + TraCI | `sumolib`, `traci` from pip |
| Data | pandas | parse XML with `lxml` |
| LLM | any API with **structured/JSON output** | pin the model name in config; log every call |
| Console | Streamlit (fast) or a small web app | Streamlit unless someone is fluent in React |
| Map | folium / pydeck / deck.gl | detectors coloured by speed |
| Charts | matplotlib for stills, console for interactive | stills go in the deck |

**Fallback if SUMO fights us (decide by 4 Oct):** hand-build a ~15-link network
with a simple queueing / BPR-style link model. It still demonstrates the circuit
effect and the plan comparison. Losing the twin is survivable; losing week 3 is
not. See `04-plan.md` §go/no-go.

---

## 6. Prompt design rules (for B, D, F)

1. **Always request a fixed JSON schema** and validate the response against it.
   A response that fails validation is retried once, then flagged, never
   silently used.
2. **Few-shot with real examples** from the archive, including awkward ones
   (empty lat/lon, empty district, Chinese-only phrasing, a procession notice
   that must be marked out of scope).
3. **Temperature low** for B (extraction). Higher is acceptable for D
   (generating diverse candidate plans) — diversity is the point there.
4. **Never ask the model for a number that the simulator can compute.**
5. **Log every call** to `evidence/ai-log/` with prompt, response, model name and
   timestamp. This is both our WorkBuddy evidence and our "responsible use"
   evidence.
6. Keep prompts in files (`src/*/prompts/*.md`), not inline strings, so they are
   reviewable and reusable.
