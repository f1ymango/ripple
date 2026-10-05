# Flow-balance SUMO run, 15 May: replay recipe, input provenance and assumption ledger

Prepared by Data on 5 October for Simulation's independent review, ahead of the
Lead's model decision this evening. It answers the three handoff gaps Simulation
listed and adds a check of both teams' results that was run this morning.

**Checked today, all on Linux (Python 3.13.16, SUMO 1.27.1). Nothing here has
been run on Windows.**

| Check | Outcome |
|---|---|
| Simulation's boundary experiment replayed at `4d6ccb5` from its own archive | Reproduced exactly: 178/242 (73.55%), every scored row identical |
| Data's flow-balance run replayed from a new clone of main `4875a85` | Reproduced exactly: 234/242 (96.7%) and 15.7% of 299, every scored row identical |
| Refreshed-speed run replayed the same way | Reproduced exactly: 236/242 (97.5%) and 13.2% of 299 |
| `twin-inputs_20260515.json` rebuilt from the raw detector cache | Byte-identical to the committed file (both variants) |
| Twelve one-at-a-time assumption tests on the flow-balance run | Section 3 |
| Recommended reviewed baseline, for Simulation to reproduce | Section 6: 231/242 (95.5%) and 15.8% of 299 |

Two corrections to the 4 October report came out of this: the network hash in
the saved result cannot be reproduced as written (section 1), and the toll-plaza
connection patch is not needed for the score and is partly unsupported
(section 3, row 1).

## 0. Are Simulation's figures right, and why the two runs differ

**Simulation's figures are right.** Replaying
`oct04-boundary-experiment-inputs.zip` (SHA-256 `1b841d7c…2fb5cc`, all listed
input hashes match) gives 178/242 GEH < 5, speed error 45.98% of 299 bins
(45.42% on the common 298), 13,622 loaded, 2,016 waiting (14.80%) and 14
wrong-lane teleports. The saved `oct03-boundaries.json` and the replay differ
only in file paths and timings. 51 Component C tests pass. The recommendation
not to adopt that run as a baseline stands.

One cosmetic point: the manifest hash for `results/twin/oct03-boundaries.json`
(`8d4f9dbe…`) is of the CRLF copy inside the zip. The committed file is LF and
hashes to `8040fdaf…`.

**The two runs share everything except the demand file and four add-ons.** Base
network, loops, observations, seed 2026, the 242 count bins and 299 speed bins
and `src/twin/evaluate.py` are the same.

**The count gap comes from the demand alone.** Data's demand on Simulation's
untouched network, with SUMO's default drivers, no speed signs and Simulation's
15-minute warm-up, scores 236/242. The add-ons move the speed error, not the
counts:

| Step, each added to the one above | GEH < 5 | Speed error | Waiting | Teleports |
|---|---|---|---|---|
| Simulation's boundary experiment | 178/242 (73.6%) | 46.0% | 2,016 of 13,622 | 14 |
| Data's demand, nothing else changed | 236/242 (97.5%) | 39.2% | 419 of 13,840 | 0 |
| + toll-plaza connection patch | 234/242 (96.7%) | 39.1% | 406 | 0 |
| + speed signs and the edge cut | 234/242 (96.7%) | 18.7% | 255 | 0 |
| + driver settings | 234/242 (96.7%) | 15.6% | 99 | 1 (collision) |
| + 30-minute warm-up (the saved run) | 234/242 (96.7%) | 15.7% | 238 of 16,601 | 0 |

**Why Simulation's demand loses bins although its fit matches the counts on
paper** (`fit-summary.json`: predicted equals target at most detectors):

1. **Westbound main line, 43 of the 64 failing bins.** The fitted routes send
   1,163 vehicles in 75 minutes out through the one-lane exit `956602972`
   (Kwun Hoi Path): 87% of what leaves edge `956602968`. Only 180 continue.
   The detectors on either side show about 24% leaving there (AID01222 1,580,
   AID01223 1,197). The exit runs at 11 km/h and the main line queues behind
   it at 4–16 km/h (run averages) for about 4 km, back through the tunnel.
   AID01223 still passes 10/10 because 1,713 vehicles are inserted on its own
   edge (`1197441904`) for the western chain. AID01214–AID01223 pass 47 of 90
   bins; in Data's run 89 of 90.
2. **The ramp before AID01109, 9 failing bins.** The fit asks for 1,009 veh/h
   at origin `26434907`; 278 vehicles entered and 984 did not. Data's run puts
   783 veh/h (the ordinary-morning net change) on the same ramp and also
   leaves 238 outside. The same merge limits both models.
3. **The 14 teleports** are routes `fit_33` (13) and `fit_35` (1). They enter
   by side road `244383597`, whose single lane leads only to exit
   `1194693247` within 98 m, but they are routed straight on.

Edits tried on Simulation's own routes, same network and evaluator:

| Edit | GEH < 5 | Waiting | Teleports |
|---|---|---|---|
| Side road carries the exit-bound route, `fit_33`/`fit_35` enter by `46108739` | 176/242 | 1,852 | 0 |
| The same, and `fit_21` starts on the ramp itself | 177/242 | 1,858 | 0 |
| Every origin edge under 100 m extended upstream | 150/242 | 3,988 | 23 |

The first edit removes every teleport but not the score, so the loss is the
fitted origin-to-exit pattern, not insertion mechanics. No small edit repaired
it.

**Data's run avoids these partly by construction, which is an assumption in
itself**: every vehicle leaves at the end of the first off-ramp edge, so an
exit can never queue back onto the main line, and the four chains are
independent (traffic leaving the main westbound chain is not the traffic
entering the western one). See rows 8 and 9 of the ledger.

## 1. Replay recipe from a fresh checkout

**Commits**

| What | Commit |
|---|---|
| Code, patches, `twin-inputs`, saved results | main `4875a85d6d9bb40070b056d6c545fecaeb2a3f9d` (flow-balance work is `257ccc4`, merged by `6461dab`, PR #43) |
| Base network, loops, observations | `results/twin/oct04-provisional-replay-inputs.zip` at `4d6ccb54fa1aac5241683f6b78ecdb7ccd0600c7` on `sim/e1-evaluation-correctness` (unchanged since `38e2edf`), SHA-256 `24c488b311b858bb8f9a320c397bb32c8bbf54a31bf9b6bc7b55afdcd87c9360` |

`oct04-boundary-experiment-inputs.zip` holds the same three files with the same
hashes and works equally well.

**Pinned settings**

- Replay day Friday 15 May 2026. Ordinary Fridays 8 May, 24 April, 17 April,
  10 April (1 May and 3 April are public holidays).
- SUMO 1.27.1, `sumolib` and `traci` 1.27.1. Python 3.13 (3.13.16 today). Not
  run on Python 3.14.3, which Simulation uses.
- Seed 2026, step 1 s, run starts 07:25, ends 08:55 (5,400 s), scored
  07:55–08:55 (12 five-minute slots), no closure, `--max-depart-delay -1`.

**Commands** (PowerShell, from an empty folder; every output path is new, so
`results/twin/oct04-flow-balance.json` is not touched):

```powershell
git clone https://github.com/f1ymango/ripple.git ripple-replay
cd ripple-replay
git checkout 4875a85d6d9bb40070b056d6c545fecaeb2a3f9d
git fetch origin sim/e1-evaluation-correctness
git checkout 4d6ccb54fa1aac5241683f6b78ecdb7ccd0600c7 -- results/twin/oct04-provisional-replay-inputs.zip
Expand-Archive results/twin/oct04-provisional-replay-inputs.zip -DestinationPath .
pip install -r requirements.txt   # the replay itself needs only sumolib==1.27.1 and traci==1.27.1

New-Item -ItemType Directory -Force sim/work/replay-oct05 | Out-Null
netconvert -s sim/work/aberdeen.net.xml -x sim/scenarios/aberdeen-flow-balance.con.xml -e sim/scenarios/aberdeen-flow-balance.edg.xml -o sim/work/replay-oct05/aberdeen.flow-balance.net.xml --lefthand true --output.street-names true

python -m src.twin.flow_balance_demand --inputs sim/scenarios/twin-inputs_20260515.json --network sim/work/replay-oct05/aberdeen.flow-balance.net.xml --out sim/work/replay-oct05/flow-balance --begin 07:25 --end 08:55
python -m src.twin.run_flow_balance --inputs-dir sim/work/replay-oct05/flow-balance --network sim/work/replay-oct05/aberdeen.flow-balance.net.xml --loops sim/work/may-diagnostic/detectors.add.xml --observations sim/scenarios/detectors.json --seed 2026 --out results/twin/replay-oct05/flow-balance.json
```

Refreshed-speed run, a separate claim (section 4):

```powershell
python -m src.twin.flow_balance_demand --inputs sim/scenarios/twin-inputs_20260515_refreshed.json --network sim/work/replay-oct05/aberdeen.flow-balance.net.xml --out sim/work/replay-oct05/flow-balance-refreshed --begin 07:25 --end 08:55
python -m src.twin.run_flow_balance --inputs-dir sim/work/replay-oct05/flow-balance-refreshed --network sim/work/replay-oct05/aberdeen.flow-balance.net.xml --loops sim/work/may-diagnostic/detectors.add.xml --observations sim/scenarios/detectors.json --seed 2026 --out results/twin/replay-oct05/flow-balance-refreshed.json
```

Three things the 4 October "Reproduce" section got wrong or left out:

- `netconvert` does not create the output folder; the `New-Item` line is needed.
- `run_flow_balance` refuses to reuse a run folder (`run-seed2026` inside
  `--inputs-dir`). Use a new `--out` folder for the demand to run again.
- The first command there (`fetch twin-inputs`) rewrites the committed input
  file. It is not part of the replay; see section 2.

**Expected hashes (SHA-256)**

| File | Expected |
|---|---|
| `sim/work/aberdeen.net.xml` (base network, from the archive) | `e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e` |
| Regenerated network, header removed (see below) | `0fad17ed85e04d4cfeb9e2b825a8fb75b78fe9d14451b93673a58c6863fa166b` |
| `…/flow-balance/demand.rou.xml` (routes) | `e507b215cb72bd958d54eeaba2182110eeddedd5e03d027b71a9ab9ed7f86432` |
| `…/flow-balance/speeds.add.xml` (speed signs, ordinary mornings) | `1363ff768df6fef0801c02cea7de29fe8682ac2218e230b3287e2ddbc7d382f2` |
| `…/flow-balance-refreshed/demand.rou.xml` | same as the routes above |
| `…/flow-balance-refreshed/speeds.add.xml` (speed signs, refreshed) | `c9a7372c377ceda5e66179224929e0fa9482893bac9933bf7aad9174981a03eb` |
| `sim/work/may-diagnostic/detectors.add.xml` (loops, from the archive) | `d0ac843e8ef99b431db28444d2131e4c7e1602aa7683f5ad69c8e7a40742ad6e` |
| `…/run-seed2026/detectors.add.xml` (loops after the edge cut) | `87eb8c61d872624f8e19286b88fa0109f16dbb60c9e8f35abe2771275345de8e` |
| `sim/scenarios/detectors.json` (observations, from the archive) | `a1d842a25ff872091b47fb3e7bcad566fe9932af0bc5452be3f79fc1462a4605` |
| `sim/scenarios/twin-inputs_20260515.json` | `fc6eb76ae378c2c2e391b01a7b0c3e2f6882522e32f2ac3452d4622b07668840` |
| `sim/scenarios/twin-inputs_20260515_refreshed.json` | `579078bde71ec631068b2646d9a70c9dfea39076b14365166887faeadb138c47` |

`Get-FileHash -Algorithm SHA256 <path>` gives these (in upper case).

**The network hash in the saved result (`9e23e7de…`) will never match.**
`netconvert` writes the time of the run and the output path into the file's
header comment, so two builds a second apart differ. Hash the file without the
header, with line endings normalised:

```powershell
python -c "import hashlib,sys;b=open(sys.argv[1],'rb').read().replace(b'\r\n',b'\n');print(hashlib.sha256(b[b.index(b'-->')+3:]).hexdigest())" sim/work/replay-oct05/aberdeen.flow-balance.net.xml
```

Two separate builds today gave `0fad17ed…` both times.

**Expected scores**

| Run | Count bins GEH < 5 | Speed error | Loaded | Entered | Waiting | Teleports |
|---|---|---|---|---|---|---|
| Ordinary-morning speeds | 234/242 (96.7%) | 15.7% of 299 (15.66) | 16,601 | 16,363 | 238 | 0 |
| Refreshed speeds | 236/242 (97.5%) | 13.2% of 299 (13.20) | 16,601 | 16,266 | 335 | 0 |

Ordinary-morning split: assessment-only detectors 96.6% of 205 and 16.6% of
252; demand-setting detectors 97.3% of 37 and 10.4% of 47. Each run takes about
20 seconds.

**Windows.** Not tested. Where a Windows run could differ without anything
being wrong: the regenerated network if `netconvert` writes CRLF (the command
above normalises it) and the result JSON's line endings. The routes and
speed-sign files are written as bytes and should match exactly. If the routes
or speed-sign hash differs, or a score differs, that is a real difference.

**For the paired replay, please send back**: the eleven hashes above, the two
score rows, and the SUMO and Python versions used.

## 2. Input provenance

**Yes: the committed `sim/scenarios/twin-inputs_20260515.json` is the starting
point for the replay.** It holds everything the detectors contribute: entry
counts at the four first detectors, the 21 ordinary-morning flow changes and
the quarter-hour speed profiles for 27 detectors. The replay needs no raw
detector data and no network access.

**An independent rebuild is possible and was checked today.** From the raw
cache, both files rebuild byte-identical to the committed ones (Linux, Python
3.10.12, at `257ccc4`). To do the same, writing to new paths:

```powershell
python -m src.loaders.fetch twin-inputs --day 2026-05-15 --ordinary-day 2026-05-08 2026-04-24 2026-04-17 2026-04-10 --out sim/work/replay-oct05/twin-inputs_20260515.json
python -m src.loaders.fetch twin-inputs --day 2026-05-15 --ordinary-day 2026-05-08 2026-04-24 2026-04-17 2026-04-10 --refresh --out sim/work/replay-oct05/twin-inputs_20260515_refreshed.json
```

- No separate fetch step is needed. The command lists the archive's snapshots
  for 07:00–10:50 on each of the five days (07:15–10:35 plus 15 minutes for the
  publishing lag) and downloads any that `data/raw/detectors/` does not hold.
  It needs `api.data.gov.hk` and about 740 snapshot requests on an empty cache.
  `fetch prefetch` works in whole days and would download far more.
- The feed is TD's `rawSpeedVol-all.xml` through the government's historical
  archive. About a third of listed snapshots are not served; that is recorded
  as a `.404` file and is expected.

**Source fingerprints.** The cache is gzipped with a timestamp, so file hashes
differ between machines. This hashes the uncompressed snapshots instead:

```python
import gzip, hashlib, pathlib
root = pathlib.Path("data/raw/detectors")
for day in ["20260515", "20260508", "20260424", "20260417", "20260410"]:
    files = sorted(p for p in root.glob(f"{day}-*.xml.gz") if f"{day}-0700" <= p.name[:13] <= f"{day}-1050")
    h = hashlib.sha256()
    for p in files:
        h.update(p.name[:13].encode()); h.update(hashlib.sha256(gzip.open(p, "rb").read()).digest())
    print(day, len(files), h.hexdigest())
```

| Day | Snapshots served | Not served | Fingerprint |
|---|---|---|---|
| 15 May | 98 | 43 | `04d78654e32b526d20953326a6087d43db46b1ae37640cddd95b5b360ad6fd05` |
| 8 May | 94 | 50 | `5fed2076120190a3eda66dfea5c9fef82b644662470693ffde07f1570f2ee910` |
| 24 April | 95 | 55 | `30a8a764e77bec8eec8872ad5ad530aa198e495387a9de1548db0ec2c8b24a83` |
| 17 April | 100 | 51 | `f68845265a97cff3cdfa9ab73f38b5d941def5ae3e3404c725e715f7792d2e9a` |
| 10 April | 95 | 55 | `4b2173734ee33d0b6f60e3c51dd86b5b0ca1b55007e8b6e72ed4dd9bea6a4fa7` |

If the archive later serves a different set of snapshots, a fingerprint will
differ and so may the rebuilt file. The rebuild has not been run from an empty
cache today.

Detector positions and the paths between detectors come from
`results/twin/osm-network-audit.json` on main (SHA-256 `4af52e21…5b741`). All
28 positions agree with Simulation's `detectors.add.csv`.

## 3. Assumption and residual ledger

Baseline for every test: the saved ordinary-morning run, 234/242, 15.7%, 238
waiting, 0 teleports. Five seeds (2026, 1, 2, 3, 4) give 232–235 of 242, 15.7%
and 147–238 waiting, so a change of one or two bins is within seed noise. Each
test changes one thing.

| # | Assumption | Support | Test | Result (GEH, speed, waiting, teleports) | Label |
|---|---|---|---|---|---|
| 1 | Toll plaza towards Wan Chai: lane 0 of `1198101424` and lanes 0–1 of `1233513875#0` connected onward | OSM tags both edges `motor_vehicle:lanes=no\|yes\|yes\|yes` and `bus:lanes=private\|yes\|yes\|yes` (franchised buses). **Simulation's objection holds for lane 0 on both edges**: it is not a general-traffic lane. Only lane 1 of `1233513875#0` is tagged open and has no onward connection. This reads OSM's left-to-right lane order as SUMO lane 0 on the nearside; Simulation to confirm | Patch left out; then only lane 1 connected | 234/242, 15.8%, 241, 0; then 234/242, 15.7%, 240, 0 | **Unsupported for lane 0, and not needed.** Drop it from any reviewed baseline |
| 2 | Edge `1198101443` cut so AID01106 and AID01107 carry separate speeds | No capacity or connection change; pieces are 12.5 m and 526.4 m | Covered by row 5 | | Modelling device for the speed signs only |
| 3 | +201 veh/h joins on the main line between TDSSPWR10003 and TDSAPR10001 | None physical: the network has no ramp there. The figure is the ordinary Fridays' net change (1,199 to 1,400 veh/h). Simulation's audit leaves the same increase unresolved | Join removed | 231/242 (95.5%), 15.8%, 218, 0 | **Inference.** Worth 3 bins |
| 4 | Entry-to-exit allocation at the Canal Road flyover: side road `244383597` carries exactly the 32.7% that leaves at the first exit `1194693247`; `46108739` carries the rest | Lane connections in the base network: the side road's lane leads only to that exit, over 23 m + 75 m. Slow-lane share at AID01214 was 29–34% (4 October report, not rechecked). No measured turning flow | Entry traffic shared by lane count instead | **206/242 (85.1%)**, 15.7%, 1,733, 17 wrong-lane at `136461565_0` | **Inference, and the result depends on it.** The failure it prevents is the one behind Simulation's 14 teleports, on the same lane |
| 5 | Imposed speed profiles: each chain edge follows the ordinary Fridays' quarter-hour speed of the detector it leads to (vehicle-weighted harmonic mean of 5-minute speeds, floor 5 km/h, lowest value used 11.2 km/h) | Measured on other days, not produced by the model | Speed signs removed | 234/242, **41.2%**, 523, 0 | **Input, not a model result.** The speed score checks the inputs against the day |
| 6 | Driver settings `speedFactor 1`, `speedDev 0.05`, `sigma 0` | Reasoning only: the imposed speeds are already stream means. No measured driver distribution; Simulation's point stands | SUMO defaults; `sigma 0.5` alone; `speedDev 0.1` alone | 234/242, 19.9%, 278; 234/242, 17.3%, 411; 235/242, 16.2%, 84 | **Tuning choice.** Worth up to 4.2 points of speed error, nothing on counts |
| 7 | 30-minute warm-up from 07:25 (Simulation uses 15) | Entry counts from 07:15 are 15 May's own, so the warm-up is measured demand | Start at 07:40 | 234/242, 15.6%, 99, 1 collision | No effect on the score |
| 8 | Lane-count splits: joins and exits shared between several ramps in one stretch (6 stretches), and the flyover split `485146392` that rejoins | None beyond lane counts | Equal shares; all flyover traffic on the main branch | 235/242, 15.8%, 195, 0; 231/242, 15.8%, 656, 0 | **Inference**, low sensitivity on counts |
| 9 | Vehicles leave at the end of the first off-ramp edge, and the four chains are independent | Structural: an exit cannot queue back, and no vehicle travels from one chain to the next | Not tested | | **Untested.** Matters most for an incident or a diversion |
| 10 | Two net changes under 5% with no ramp are left out (+58 veh/h AID01106 to AID01107, +44 veh/h TDSSPWR10002 to TDSSPWR10003) | Builder rule | Not tested | | Disclosed omission |

All alternatives together (rows 1, 3, 4, 6, 7, 8): 205/242 (84.7%), 17.2%,
1,448 waiting, 14 teleports. Row 4 accounts for nearly all of it.

**Residuals to keep visible**

- **238 vehicles waiting to enter (1.4%).** All 238 are on ramp `46766432`,
  the signal-controlled merge between AID01108 and AID01109 (confirmed today
  from the trip records). That is over Data's proposed 1% gate. Refreshed run:
  335 (2.0%).
- **Eight failing count bins**, observed against simulated: AID01104 08:50
  (42, 96: the accident's first minute); AID01106 08:05 (85, 152) and 08:15
  (75, 128); AID01223 07:55 (70, 122); TDSSPWR10001 08:10 (25, 66);
  TDSSPWR10003 08:15 (55, 104); TDSAPR10001 08:05 (162, 104) and 08:10
  (185, 117).
- **The 5-minute GEH is forgiving.** On each detector's total for the hour,
  19 of 25 detectors are within GEH 5 (Simulation's run: 12 of 25). Outside:
  AID01106 +23%, AID01109 −14%, TDSAPR10001 −13%, AID01216 −12%, AID01215
  −11%, AID01221 −11%. All detectors together: 33,620 simulated against 34,850
  observed (−3.5%).
- **Speed error by detector**: AID01106 72.1%, AID01216 48.5%, AID01108 33.1%,
  AID01109 25.2%, TDSSPWR10001 22.5%.
- **The 4 October report's sentence that further tuning "will not move" the
  speed figure is too strong**, as Simulation said. It holds for this
  prescribed-speed setup only (row 5).

## 4. What each result can be quoted for

| Claim | Figures | Built from | Not to be quoted as |
|---|---|---|---|
| Ordinary-morning replay | 234/242 (96.7%), 15.7% of 299, 238 waiting | Four other Fridays, plus 15 May's own counts at the four first detectors | A calibrated network, or a speed model: the speeds are imposed |
| Refreshed-speed replay | 236/242 (97.5%), 13.2% of 299, 335 waiting | The same, plus every detector's own speed from the previous quarter-hour | A calibration from ordinary mornings. It is a 15-minute-ahead forecast and no detector is held out for speed |

Neither run applies a closure. Neither shows queue formation, spillback,
recovery or diversion. Incident queue and recovery validation is the next,
separate test, and the 96.7% does not establish it.

## 5. Suggested points for this evening

1. Accept or reject row 4 (the Canal Road entry rule). It is the one
   inference the count score rests on.
2. Drop the connection patch (row 1) unless Simulation confirms the lane
   interpretation; the score does not need it.
3. Decide how the +201 veh/h in row 3 is described, or accept 231/242 without
   it.
4. Decide whether the count target is read on 5-minute bins or on hourly
   totals.
5. Agree the incident check for whichever model is chosen: row 9 has to be
   settled first for this one.

## 6. Recommended reviewed baseline, for Simulation to reproduce

Data's recommendation for this evening: keep the flow-balance demand, and give
way on the two assumptions that have no support. Added 5 October after the
checks above.

| Assumption | Recommended | Why |
|---|---|---|
| Demand (where traffic enters and leaves) | Data's | Simulation's fitted routes match the counts on paper but send 87% of westbound traffic out of one single-lane exit, which jams the run (section 0) |
| Canal Road entry rule (row 4) | Data's, labelled as an inference | The network's lane connections support it, and without it both models fail on the same lane |
| Toll-plaza lane 0 connection (row 1) | Simulation's: leave it unconnected | OSM tags it as a franchised-bus lane, and leaving it out costs nothing |
| +201 veh/h joining with no ramp (row 3) | Simulation's: drop it | Nothing physical supports it. It costs 3 bins on the western chain, away from the incident |
| Speed signs (row 5) | Data's, for the no-closure baseline only | They bring the speed error from about 41% to 15.8%, but they are inputs, not model behaviour |
| Driver settings (row 6) | Data's with speed signs; SUMO's defaults without | Data's settings only make sense when the speeds are imposed |
| Warm-up (row 7) | Either | 30 or 15 minutes gives the same score |

**Two files carry the two changes**, both added on this branch
(`data/replay-handoff-oct05`), so nothing in the code changes:

| File | What it is | SHA-256 |
|---|---|---|
| `sim/scenarios/aberdeen-flow-balance-buslane.con.xml` | Connection patch without lane 0: only lane 1 of `1233513875#0` is connected and lane 2 moved over | `d259c1ab989bf7ed37dfe38beccdf20a6ebe10c8642fe9e78d65fb6979e3a676` |
| `sim/scenarios/twin-inputs_20260515_no-mainline-join.json` | The committed `twin-inputs_20260515.json` with one value changed: `join_veh_h` for TDSSPWR10003 to TDSAPR10001 set from 201.2 to 0.0 | `fbc71ca5696238006dd42403d0f4783cab1ad50664d34f5087c56eed6fbe8e1f` |

**Commands**, after section 1's setup (clone, archive, `replay-oct05` folder),
with this branch checked out instead of main `4875a85`, or with the two files
copied in:

```powershell
netconvert -s sim/work/aberdeen.net.xml -x sim/scenarios/aberdeen-flow-balance-buslane.con.xml -e sim/scenarios/aberdeen-flow-balance.edg.xml -o sim/work/replay-oct05/aberdeen.flow-balance-buslane.net.xml --lefthand true --output.street-names true

python -m src.twin.flow_balance_demand --inputs sim/scenarios/twin-inputs_20260515_no-mainline-join.json --network sim/work/replay-oct05/aberdeen.flow-balance-buslane.net.xml --out sim/work/replay-oct05/reviewed --begin 07:25 --end 08:55
python -m src.twin.run_flow_balance --inputs-dir sim/work/replay-oct05/reviewed --network sim/work/replay-oct05/aberdeen.flow-balance-buslane.net.xml --loops sim/work/may-diagnostic/detectors.add.xml --observations sim/scenarios/detectors.json --seed 2026 --out results/twin/replay-oct05/reviewed.json
```

The same with the speed signs off (add `--no-speeds`, new folders):

```powershell
python -m src.twin.flow_balance_demand --inputs sim/scenarios/twin-inputs_20260515_no-mainline-join.json --network sim/work/replay-oct05/aberdeen.flow-balance-buslane.net.xml --out sim/work/replay-oct05/reviewed-no-signs --begin 07:25 --end 08:55 --no-speeds
python -m src.twin.run_flow_balance --inputs-dir sim/work/replay-oct05/reviewed-no-signs --network sim/work/replay-oct05/aberdeen.flow-balance-buslane.net.xml --loops sim/work/may-diagnostic/detectors.add.xml --observations sim/scenarios/detectors.json --seed 2026 --out results/twin/replay-oct05/reviewed-no-signs.json
```

**Expected hashes** (run today from a new clone, Linux only)

| File | Expected |
|---|---|
| Regenerated network, header removed (section 1's command) | `c11501968dc3d15235f23c6802f0be9551b03743ef0a81eecf6f28ed26c23937` |
| `…/reviewed/demand.rou.xml` | `9fc839b2c6cf11360520b89463b7880dbb56bb5b8c962cf5a75460782f7b2857` |
| `…/reviewed/speeds.add.xml` | `53b247a9471f9e2e62acc8ff6f8d44f9811fd97cf019d609af15502d864585a7` |
| `…/reviewed-no-signs/demand.rou.xml` | same as the routes above |
| `…/reviewed-no-signs/speeds.add.xml` (empty) | `2bc3ed19d77d67e8318ca3ec67dfcdb454194eeb127ec3068267a7865397d437` |

Base network, loops and observations are those of section 1.

**Expected scores**

| Run | Count bins GEH < 5 | Speed error | Loaded | Entered | Waiting | Teleports |
|---|---|---|---|---|---|---|
| Reviewed baseline, speed signs on | 231/242 (95.5%) | 15.8% of 299 (15.78) | 16,299 | 16,077 | 222 | 0 |
| The same, speed signs off | 233/242 (96.3%) | 41.2% of 299 | 16,299 | 15,776 | 523 | 0 |

Reviewed baseline split: assessment-only detectors 95.1% of 205 and 16.7% of
252; demand-setting detectors 97.3% of 37 and 10.6% of 47. On hourly totals,
19 of 25 detectors are within GEH 5. Eleven bins fail: the eight of section 3
plus AID01109 08:00, TDSSPWR10002 08:50 and TDSAPR10001 08:00 (TDSAPR10001 is
where the dropped join used to enter).

The signs-off run keeps Data's driver settings, because the builder has no
switch for them. With SUMO's default drivers as well (a one-line change to
`VTYPE` in `flow_balance_demand.py`, in the evidence zip as
`recommended_nospeeds`) it gives 233/242, 40.1% and 518 waiting.

**What this baseline still does not cover.** It is a no-closure run. For the
incident the speed signs have to come off, at least on the incident chain, so
that the queue forms by itself; the signs-off row shows the counts hold and
the speeds do not. Row 9 (exits end at the first off-ramp, chains
independent) remains untested and decides whether this base can carry a
diversion.

Evidence for sections 0 and 3 (variant scripts, route files and every result
JSON) is in `ripple-oct05-review-evidence.zip`, held by Data outside the
repository; it can be committed or shared on request. Component C tests on
main: 53 pass, 18 of them the flow-balance ones.
