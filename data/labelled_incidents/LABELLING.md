# Labelling the gold set

The Incident Reader's accuracy number (component B, `docs/00-brief.md` §4) is
measured on about 100 real Special Traffic News messages, each with a
hand-written answer. This file says how to make that set and how to label it,
so that two people labelling the same message write the same answer.

| File | What it is |
|---|---|
| `messages.jsonl` | The **dev set**: 20 messages, read freely while working on the prompt. |
| `gold_messages.jsonl` | The **gold set**: messages the prompt was never tuned on. |
| `gold_labels.jsonl` | One hand-written label per gold message. |
| `history/gold_labels_v1.jsonl` | The labels as they stood for the held-out v1 score (see Score history). |

## Rules that keep the number honest

1. **Label from the message alone.** Do not run the Reader on the gold set
   until every message is labelled, and never label with its output open. The
   labelling app never shows it.
2. **Do not tune the prompt on the gold set.** Once a gold score has been
   seen, a prompt change afterwards makes the next score optimistic. If the
   prompt must change, say so next to the number, or label a fresh set.
3. **Hard cases stay in.** Skipping a message because it is awkward makes the
   number look better than the Reader is. Mark it `unsure` and write why.

## Steps

**1. Make the gold messages** (once; the file is committed afterwards):

```bash
python -m src.loaders.fetch prefetch --feed stn --start 2026-06-22 --end 2026-09-21
python -m src.reader.sample --start 2026-06-22 --end 2026-09-21 --n 80 --corridor 20 \
    --exclude data/labelled_incidents/messages.jsonl \
    --out data/labelled_incidents/gold_messages.jsonl
```

The first command downloads about 9,700 STN snapshots (about 20 minutes, and
it can be resumed); the candidate screen reads the same cache. The second
writes 80 `citywide` messages (a random sample of incidents off the corridor)
and 20 `corridor` messages (incidents that name an Aberdeen corridor road,
too rare to turn up at random). It leaves out every dev-set incident and the
prompt's worked examples.

**2. Label them:**

```bash
streamlit run src/reader/label.py
```

One message at a time; **Save and next** writes `gold_labels.jsonl`
straight away, so you can stop and come back. Allow about a minute per
message. Commit the labels file as you go.

**3. Score a run** (only after every message is labelled):

```bash
python -m src.reader.run --messages data/labelled_incidents/gold_messages.jsonl
python -m src.reader.score --run results/reader/<run_id>.jsonl
```

## How to label each field

A label is the answer the contract asks for (`docs/03-architecture.md` §3),
following the same rules as the Reader's prompt (`src/reader/prompts/system.md`).
If this file and the prompt ever disagree, stop and make them agree before
labelling on: the Reader cannot be marked wrong for a rule it was never given.

Leave a text box **blank** when the message does not say; that is saved as
`null`. Read both languages: when the English and Chinese disagree, label
from the English and say so in the comment.

- **road_name**: the road the incident is on, as its official English name,
  as the message writes it. A bracket after the road that names a section of
  it rather than a direction is part of the name: "Tsing Long Highway (Ting
  Kau Bridge) (Kowloon bound)" → `Tsing Long Highway (Ting Kau Bridge)`. If
  the message lists several roads ("The following road sections are busy:
  ..."), the first one. Blank if it names no road.
- **direction**: the direction of travel affected, as `<place> bound`, from
  the bracket after the road: "(Central bound)" → `Central bound`. "(both
  bounds)" → `both directions`. Blank if not stated.
- **near_landmark**: what follows "near": "near Percival Street" →
  `Percival Street`. Blank if none.
- **between_landmark**: `X and Y` when the message says "between X and Y".
  Blank otherwise.
- **incident_type**: exactly one of
  - `traffic_accident`: a traffic accident.
  - `vehicle_breakdown`: a vehicle breakdown.
  - `road_works`: road works, including watermain works and emergency repairs.
  - `flooding`: flooding, including a burst watermain.
  - `object_on_road`: obstacles, fallen trees, fallen scaffolding, spilled load.
  - `public_event`: processions, marches, races and other public events.
  - `public_transport_notice`: the message is **only** about bus, ferry, rail
    or other public transport services, e.g. services resuming. A message
    that reports a road or lane closure, or its re-opening, takes the
    closure's cause, even if it also says bus routes are affected.
  - `other`: anything else, e.g. heavy traffic, a fire, or a cause given only
    as "road incident" (道路事故), which does not say what happened. Take the
    cause from the message text, not the "Road Incident" heading every
    message carries.
- **lanes_closed**: the lanes closed **as of this message**.
  - "the fast lane" → `fast`; "the slow lane" → `slow`; "the hard shoulder"
    → `hard_shoulder`.
  - One middle lane ("the middle lane") → `middle1`. Two middle lanes:
    `middle2` is next to the fast lane, `middle1` next to the slow lane.
  - "all lanes of ... are closed" → `all`. "Closed to all traffic" means
    closed to every vehicle, **not** that every lane is closed.
  - "part of the lanes ... is closed" → `unspecified`. Never pick lanes the
    message does not name.
  - `all` and `unspecified` are never combined with another value.
  - Leave it **empty** when the lanes have re-opened, when nothing is closed
    (e.g. busy traffic), and for an arrangement that fits none of the values
    (a one-lane-two-way arrangement, a closed slip road): describe that in the
    comment.
- **lanes_total**: the number of lanes in the affected direction, **only** if
  the message states it or it follows directly: one named lane closed and
  "only remaining lane" → 2; two named lanes closed and "only remaining lane"
  → 3. `unspecified` or `all` with "only remaining lanes" does not say how
  many: blank. Never use your own knowledge of the road.
- **unsure**: tick when you could not decide, and write why in the comment.
- **comment**: anything a second labeller should know. Never scored.

The model's `confidence` and `notes` are its own opinion, so they are not
labelled; the other contract fields are copied from the feed by code.

## How it is scored

Fixed before any gold score was seen, in `src/reader/score.py`:

- Text fields match after trimming, collapsing spaces and ignoring case:
  `Aberdeen  tunnel` matches `Aberdeen Tunnel`. Nothing looser.
- `lanes_closed` matches as a set; every other field must be equal
  (blank matches only blank).
- A message the Reader flagged counts as wrong on every field.
- `unsure` labels are scored like the rest, and counted in the report.
- Each figure comes with a 95% interval. The `citywide` figure is the
  headline, the `corridor` one is what the demo depends on, and each is
  reported separately as well as together.

## Score history

"All fields right" per message; 95% intervals in brackets. Every figure is a
file in `results/reader/`, written by `src/reader/score.py`.

| Version | Prompt | Labels | Citywide (80) | Corridor (20) |
|---|---|---|---|---|
| **v1, held out** (25 Sep) | as merged in #9 | first pass, final before any score | **50%** (39–61%) | **75%** (53–89%) |
| v2 (25 Sep) | `bound` kept in direction | 4 corrected after v1 was seen | 75% (64–83%) | 85% (64–95%) |

**v1** is the held-out number: labels final (`history/gold_labels_v1.jsonl`)
and matching rules fixed before the Reader's output was looked at.
Files: `2026-09-25T0026_qwen3-8b_score.json`.

**What changed after v1 was seen**, so v2 is *not* a held-out number:

- **The prompt.** The 24 Sep road_name example dropped "(Kowloon bound)"
  without saying where it goes, and the model learned to drop `bound` from
  direction. The fix was found and checked on the dev set alone (directions
  with `bound`: 19/19 on 22 Sep, 13/19 on 24 Sep, 19/19 after the fix).
- **Four labels**, each a slip against the rules above, found because the
  Reader disagreed with them, so every one moves the score in its favour:
  144214 (an arrangement "now cancelled": lanes empty), 144622 and 146041
  ("leading to X" is not a stated direction: blank), 144352 (only about ferry
  sailings: `public_transport_notice`).

Almost all of the gain is the prompt fix: the v2 run scored against the v1
labels gives 59/80 citywide (74%) and 16/20 corridor
(`2026-09-25T0048_qwen3-8b_score_labels-v1.json`); the label corrections add
one message on each side (`2026-09-25T0048_qwen3-8b_score.json`). The fix also
lost three fields the v1 run had right. Quote v2 next to v1, never alone. A
new held-out number needs a fresh set, labelled after the gaps below are
settled.

**Known Reader errors left in v2**: one named lane closed with "only
remaining lanes are" (plural) gets `lanes_total` 2, which the message does
not say (7 of 100); a road junction ("the junction of X and Y") becomes road
X with Y as a landmark or direction; `near_landmark` filled where the message
has no "near" (7 of 100).

**Gaps to settle before labelling another set**: road junctions; a traffic
advisory that also announces extra public transport service.

## Decided cases

When the rules above do not settle a message, choose the reading an operator
would need, then add one line here so every later case is labelled the same
way. Examples come from the dev set, never from the gold set.

- "Part of the lanes of X ... which was closed ... is re-opened" →
  `lanes_closed` empty, `lanes_total` blank (IN-26-06852).
- "part of the lanes ... is closed ... Only remaining lanes are available" →
  `unspecified`, `lanes_total` blank (IN-26-06898).
- "Due to road incident , all lanes of Tung Chung Road (both bounds) ... are
  closed ... Services of LWB routes ... have been affected" → `other` (the
  cause is only "road incident"; a closure, so not a public transport
  notice), `all`, `both directions` (IN-26-06846).
- "Tsing Long Highway (Ting Kau Bridge) (Kowloon bound)" → road_name
  `Tsing Long Highway (Ting Kau Bridge)`, direction `Kowloon bound`
  (IN-26-06774). The same holds for any bracket that names a place on the
  road, such as a bridge or a roundabout: it is part of road_name, never
  near_landmark (decided 25 Sep).
- "The slow lane of X ... which was closed ... is re-opened": `lanes_closed`
  is **empty**, even though the message names the lane. It names the lane
  that *was* closed (decided 25 Sep, after the first gold pass labelled 40 of
  these with the lane).
- "between X and Y" counts in any message, a public transport notice
  included: a rail fault between two stations → between_landmark
  `X and Y`, with the stations as the message names them (decided 25 Sep).
