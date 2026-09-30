# Backup network: the ~15-link fallback

For the go/no-go on Sun 4 Oct ([docs/04-plan.md](../../docs/04-plan.md)): if the
SUMO twin's baseline does not roughly match the detectors, the team switches to
this network. It is a cell transmission model (Daganzo, 1994) of the corridor's
four detector chains: 24 links from one detector to the next, plus a 200 m
approach to each chain's first detector. Pure Python, no SUMO; the 15 May
replay takes about 35 seconds.

```bash
python -m src.fallback.run --day 2026-05-15 --ordinary-day 2026-05-08 2026-04-24
```

It reads the detector archive cache (fill it with the data layer, as for the
twin) and writes
[results/fallback/replay_20260515.md](../../results/fallback/replay_20260515.md)
and `.json`.

## Result, 15 May (IN-26-03365)

Pre-incident hour 07:55–08:55, scored as `src/twin/evaluate.py` scores SUMO:
GEH < 5 on the usable 5-minute counts (40% archive coverage, 90% of lane
readings valid) and speed MAPE on 5-minute bins.

| Scored on | GEH < 5 | Speed error | Ordinary mornings' own error |
|---|---|---|---|
| All detectors | 97.1% of 242 bins | 16.6% | 16.6% |
| Detectors inside the chains | 97.1% of 205 bins | 17.8% | 17.8% |
| SUMO, 27 Sep diagnostic | 66.5% of 242 bins | 36.9% | |

Targets: GEH < 5 for at least 85% of counts, speed error about 15% or less
([docs/03-architecture.md](../../docs/03-architecture.md) §4).

- *Inside the chains* leaves out the four first detectors, which are fed
  15 May's own counts. Nothing else in the network comes from 15 May.
- *Ordinary mornings' own error*: predict every 5-minute speed on 15 May with
  the ordinary mornings' average at that detector. The network adds no error of
  its own before the incident; to beat this figure a model has to reproduce
  15 May's own queues, at AID01106 and AID01216 above all.
- The incident: the queue reaches AID01104, AID01103 and AID01102 within
  5 minutes of the detectors, but AID01101 25 minutes early, and it has not
  cleared by 10:35. Nobody diverts yet (below).

## Where every number comes from

| Input | Source |
|---|---|
| Link length | the OSM path between the two detectors, from Simulation's audit ([results/twin/osm-network-audit.json](../../results/twin/osm-network-audit.json)) |
| Lanes | TD's feed at the two detectors, the fewer of the two; OSM's count where the feed has none |
| Speed | the ordinary mornings' average, 07:55–08:55 and weighted by vehicles, at the detector the link ends at, or at the one before where that one is silent |
| Joins and exits | the ordinary mornings' net flow change between neighbouring reporting detectors, placed halfway along the link into the downstream one |
| Capacity | 1,800 veh/h per lane: an assumption |
| Stopped traffic | 140 vehicles per km per lane, about 7 m each: an assumption |
| Traffic arriving | at each chain's first detector, in 15-minute steps: the replay morning's own counts until 09:00, then the ordinary mornings' average (after 09:00 a first detector may be counting a queue) |
| Incident | slow lane blocked from 08:54, passing 360 veh/h (what the fast lane carried past it, [lane evidence](../../results/data/lane-evidence_AID01104_20260515-0840_0920.md)); all lanes from 09:00; re-opened 10:02 (TD); 90% of the way from AID01103 to AID01104 |

Simplifications, to state with the results:

- traffic joins and leaves halfway between two detectors, because the
  detectors only show that it happens somewhere in between;
- leaving traffic has its own slip road, so it keeps leaving while the road
  ahead is queued, and traffic going further never leaves early;
- no ordinary-day bottlenecks: an ordinary morning's slowdowns are already in
  the link speeds, so queues come only from the incident;
- nobody diverts. While the flyover was shut the detectors show traffic still
  moving past AID01101–AID01103 and leaving the corridor (the replay's "flow
  while all lanes closed"); in the model everyone waits for the re-opening.
  The incident's delay and queue length are therefore an upper bound until the
  week 3 diversion routes are in.

## Files

- `ctm.py`: the traffic model. Tests in
  [tests/test_fallback.py](../../tests/test_fallback.py), with no network access.
- `network.py`: builds the four chains from the files above.
- `run.py`: replays a morning, scores it and writes the report.

For the Evaluator (E, week 3): a plan's closures are
`Closure(link, start_s, end_s, capacity_veh_h, at)` passed to `Corridor.run`,
which returns counts and speeds per detector per 5 minutes, the delay in
vehicle-hours, the longest queue and the vehicles still waiting to enter.
Diversion is the piece still to add.
