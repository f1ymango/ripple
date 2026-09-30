"""The backup network: what its traffic model must never get wrong, and how it is built and scored."""
import datetime as dt
import math

import pytest

from src.fallback import network, run
from src.fallback.ctm import Closure, Corridor, Link, Result
from src.loaders.common import HK

HOUR = 3600


def _road(n_links=3, length=1000.0, lanes=2, speed=72.0, capacity=3600.0, **kw):
    """Detectors D0 -> D1 -> ... with identical links between them."""
    return Corridor("D0", [Link(f"L{k}", length, lanes, speed, capacity, ends_at=f"D{k + 1}", **kw)
                           for k in range(n_links)])


def _steady(result, detector, first_bin=4):
    """Mean count per 5-minute bin once the road has filled."""
    counts = result.counts[detector][first_bin:-1]
    return sum(counts) / len(counts)


def test_light_traffic_flows_through_at_free_speed():
    r = _road().run(lambda t: 720, end_s=HOUR)
    assert _steady(r, "D3") == pytest.approx(60, abs=0.5)          # 720 veh/h = 60 per 5 min
    assert r.speeds["D3"][6] == pytest.approx(72, abs=0.1)
    assert r.delay_vehicle_hours == pytest.approx(0, abs=0.5)
    assert max(r.max_queue_m.values()) == 0 and r.longest_queue_m == 0


def test_every_vehicle_is_accounted_for():
    road = _road(join_veh_h=300, exit_share=0.2)
    r = road.run(lambda t: 2400, end_s=HOUR, closures=[Closure("L2", 900, 1800, 0)])
    assert r.entered == pytest.approx(r.left + r.in_corridor_at_end + r.waiting_at_end, rel=1e-9)


def test_a_bottleneck_holds_flow_to_its_capacity_and_the_queue_grows_back():
    road = _road(n_links=3, capacity=3600.0)
    road.end_capacity = 1200.0                                        # the far end takes 1,200 veh/h
    r = road.run(lambda t: 1800, end_s=HOUR)
    assert _steady(r, "D3") == pytest.approx(100, abs=1)             # 1,200 veh/h out
    assert r.speeds["D3"][-2] < 40                                     # queued at the end
    assert r.max_queue_m["L2"] > 900                                  # the last link fills up
    assert r.speeds["D1"][-2] < r.speeds["D1"][1]                     # and it reaches back upstream


def test_a_closure_stops_traffic_then_the_queue_discharges_at_capacity():
    road = _road(capacity=2400.0)
    r = road.run(lambda t: 1800, end_s=2 * HOUR, closures=[Closure("L1", 1800, 2700, 0)])
    during = r.counts["D2"][7:9]                                     # 35-45 minutes in
    assert max(during) < 1
    after = r.counts["D2"][10:13]                                    # the queue empties at capacity
    assert all(c == pytest.approx(200, abs=2) for c in after)         # 2,400 veh/h = 200 per 5 min
    assert r.counts["D1"][8] < r.counts["D1"][2]                     # the queue passed back over D1
    assert r.max_queue_m["L1"] > 900 and r.max_queue_m["L0"] > 900
    assert r.longest_queue_m > 1800                                   # one queue, across both links


def test_traffic_already_past_the_blockage_drives_away():
    road = _road(capacity=2400.0)
    r = road.run(lambda t: 1800, end_s=HOUR, closures=[Closure("L1", 1800, 3600, 0, at=0.5)])
    assert r.counts["D2"][6] > 0 and max(r.counts["D2"][8:]) < 1      # drains, then nothing
    assert r.speeds["D2"][6] == pytest.approx(72, abs=0.5)            # at free speed, not stuck


def test_a_side_road_adds_and_an_exit_removes_between_detectors():
    r = _road(n_links=1, join_veh_h=360).run(lambda t: 720, end_s=HOUR)
    assert _steady(r, "D1") == pytest.approx(90, abs=0.5)             # (720 + 360) / 12
    r = _road(n_links=1, exit_share=0.25).run(lambda t: 720, end_s=HOUR)
    assert _steady(r, "D1") == pytest.approx(45, abs=0.5)             # 720 * 0.75 / 12


def test_merging_traffic_shares_the_room_by_demand():
    road = _road(n_links=1, capacity=1800.0, join_veh_h=900)
    road.end_capacity = 1800.0
    r = road.run(lambda t: 1500, end_s=HOUR)
    assert _steady(r, "D1") == pytest.approx(150, abs=1)             # capped at 1,800 veh/h
    assert r.waiting_at_end > 0                                       # both approaches queue


def test_the_step_shrinks_so_short_links_still_get_two_cells():
    road = Corridor("A", [Link("short", 120.0, 2, 72.0, 3600.0, ends_at="B")], dt_s=5.0)
    assert road.dt <= 120.0 / (2 * 20.0) and len(road.cell_link) >= 2


def test_a_detector_that_sees_no_vehicle_reports_no_speed():
    r = _road().run(lambda t: 0, end_s=900)
    assert r.speeds["D3"] == [None, None, None]


def test_leaving_traffic_keeps_leaving_but_through_traffic_never_leaks_out():
    road = _road(n_links=2, capacity=2400.0, exit_share=0.5)          # half leave on each link
    r = road.run(lambda t: 1200, end_s=HOUR, closures=[Closure("L1", 900, HOUR, 0)])
    assert r.max_queue_m["L1"] > 900 and r.max_queue_m["L0"] > 100    # the queue passes both slip roads
    assert r.left >= 0.5 * r.entered                                  # the first slip road stays free
    assert r.left <= 0.75 * r.entered + 1e-6                          # a quarter are bound past both exits
    assert max(r.counts["D2"][4:]) < 1                                # and none of them gets out


# ---------------------------------------------------------------- the network

NO_DATA = ("AID01105", "AID01220", "TDSSPWR20002")     # in the chains, silent in the feed


def _typical(flows=None, speeds=None):
    """Two identical ordinary mornings: 1,000 veh/h at 60 km/h unless given, nothing at NO_DATA."""
    ids = {d for chain in network.CHAINS.values() for d in chain} - set(NO_DATA)
    return {d: network.Ordinary([(flows or {}).get(d, 1000.0)] * 2, [(speeds or {}).get(d, 60.0)] * 2)
            for d in ids}


def test_the_network_follows_the_detector_chains():
    corridors, table = network.build(_typical())
    lengths, lanes = network.audit()
    for name, chain in network.CHAINS.items():
        links = corridors[name].links
        assert [l.ends_at for l in links] == chain                    # an approach, then detector to detector
        assert links[0].length_m == network.APPROACH_M
        for (up, down), link in zip(zip(chain, chain[1:]), links[1:]):
            assert link.id == f"{up}->{down}" and link.length_m == lengths[(up, down)]
            assert link.lanes == min(lanes[up], lanes[down])
            assert link.capacity_veh_h == link.lanes * network.LANE_CAPACITY_VEH_H
    assert len(table) == sum(len(chain) for chain in network.CHAINS.values())


def test_speeds_joins_and_exits_come_from_the_ordinary_mornings():
    flows = {"AID01101": 1000, "AID01102": 1300, "AID01103": 1040, "AID01104": 1040, "AID01106": 1560}
    corridors, _ = network.build(_typical(flows, speeds={"AID01104": 50.0, "AID01106": 30.0}))
    links = {l.id: l for l in corridors["main_eastbound"].links}
    assert links["AID01101->AID01102"].join_veh_h == pytest.approx(300)
    assert links["AID01102->AID01103"].exit_share == pytest.approx(0.2)        # 260 of 1,300 leave
    assert links["AID01103->AID01104"].join_veh_h == 0 and links["AID01103->AID01104"].exit_share == 0
    # AID01105 reports nothing: the change from AID01104 lands on the link into AID01106,
    # and the link into AID01105 drives at AID01104's speed
    assert links["AID01104->AID01105"].join_veh_h == 0 and links["AID01104->AID01105"].exit_share == 0
    assert links["AID01105->AID01106"].join_veh_h == pytest.approx(520)
    assert links["AID01104->AID01105"].free_speed_kmh == 50.0
    assert links["AID01105->AID01106"].free_speed_kmh == 30.0


# ---------------------------------------------------------------- the replay

START = dt.datetime(2026, 5, 15, 7, 25, tzinfo=HK)      # half an hour before the scored hour
BINS = 38                                               # to 10:35


def _clock(b):
    return (START + dt.timedelta(minutes=5 * b)).strftime("%H:%M")


def _bin(clock):
    return next(b for b in range(BINS) if _clock(b) == clock)


def test_geh():
    assert run.geh(100, 100) == 0 and run.geh(0, 0) == 0
    assert run.geh(150, 100) == pytest.approx(math.sqrt(20))


def test_what_got_past_the_blocked_slow_lane_comes_from_the_lane_evidence():
    assert run.slow_lane_capacity() == pytest.approx(360)


def test_the_score_keeps_each_chains_first_detector_apart():
    result = Result(300, {"A": [100.0] * BINS, "B": [100.0] * BINS}, {"A": [60.0] * BINS, "B": [60.0] * BINS},
                    {}, 0, 0, 0, 0, 0, 0)
    obs = {}
    for b in range(BINS):
        obs[("A", _clock(b))] = {"count_bin": 100, "speed_kmh": 60.0}
        obs[("B", _clock(b))] = {"count_bin": 150, "speed_kmh": 50.0}     # GEH 4.5; the model 20% fast
    typical = {"A": network.Ordinary([1200.0] * 2, [60.0] * 2), "B": network.Ordinary([1200.0] * 2, [55.0] * 2)}
    s = run.score({"chain": result}, obs, {"A"}, START, typical)
    assert s["per_detector"]["A"]["first_of_chain"] and not s["per_detector"]["B"]["first_of_chain"]
    assert s["per_detector"]["B"]["count_bins"] == 12                          # 07:55 to 08:55 only
    inside, everything = s["inside_the_chains"], s["all_detectors"]
    assert inside["geh_under_5_pct"] == 100.0 and inside["count_bins"] == 12
    assert inside["speed_mape_pct"] == 20.0
    assert inside["ordinary_speed_mape_pct"] == 10.0                            # 55 against 50
    assert everything["speed_mape_pct"] == 10.0 and everything["count_bins"] == 24


def test_the_incident_table_reads_when_the_queue_arrived_and_cleared():
    chain = network.CHAINS["main_eastbound"]
    speeds = {d: [60.0] * BINS for d in chain}
    counts = {d: [100.0] * BINS for d in chain}
    obs = {(d, _clock(b)): {"speed_kmh": 60.0, "flow_veh_h": 1200} for d in chain for b in range(BINS)}
    for b in range(_bin("09:10"), _bin("10:15")):                    # observed: slow 09:10, clear 10:15
        obs[("AID01102", _clock(b))]["speed_kmh"] = 10.0
    for b in range(_bin("09:00"), BINS):                              # model: nothing passes from 09:00,
        counts["AID01102"][b] = 0.0
    for b in range(_bin("09:05"), BINS):                              # slow from 09:05, never clear
        speeds["AID01102"][b] = 12.0
    obs[("AID01102", "09:30")]["flow_veh_h"] = ""                    # an unusable count is left out
    result = Result(300, counts, speeds, {}, 0, 0, 0, 0, 0, 0)
    table = {x["detector"]: x for x in run.incident_upstream(result, obs, chain, START)}
    assert list(table) == ["AID01101", "AID01102", "AID01103", "AID01104"]   # up to the blockage
    row = table["AID01102"]
    assert row["queue_reached"] == {"observed": "09:10", "model": "09:05"}
    assert row["cleared"] == {"observed": "10:15", "model": None}
    assert row["flow_while_closed_veh_h"] == {"observed": 1200, "model": 0, "bins": 11}   # 09:00-09:55
    assert table["AID01101"]["queue_reached"] == {"observed": None, "model": None}


def _readings(day, detector, clock_from, clock_to, flow):
    """One 30-second lane reading a minute, as the archive delivers them, at `flow` veh/h."""
    t, end, rows = dt.datetime.combine(day, clock_from, HK), dt.datetime.combine(day, clock_to, HK), []
    while t < end:
        rows.append({"timestamp": t, "detector_id": detector, "direction": "", "lane": "Slow Lane",
                     "speed_kmh": 60.0, "volume": flow * 30 / 3600, "occupancy_pct": 10.0, "speed_sd": None,
                     "valid": True, "period_s": 30})
        t += dt.timedelta(minutes=1)
    return rows


def test_entry_demand_is_the_replay_morning_until_nine_then_the_ordinary_mornings():
    day, others = dt.date(2026, 5, 15), [dt.date(2026, 5, 8), dt.date(2026, 4, 24)]
    rows = {day: _readings(day, "E", dt.time(8, 30), dt.time(9, 30), 1200),
            others[0]: _readings(others[0], "E", dt.time(8, 30), dt.time(9, 15), 900),
            others[1]: _readings(others[1], "E", dt.time(8, 30), dt.time(9, 15), 1100)}
    start, end = (dt.datetime.combine(day, t, HK) for t in (dt.time(8, 30), dt.time(9, 30)))
    steps, source = run.entry_demand("E", rows, day, start, end)
    assert steps == pytest.approx([1200, 1200, 1000, 1000])
    assert source == ["replay morning", "replay morning", "ordinary mornings", "gap: nearest step"]
