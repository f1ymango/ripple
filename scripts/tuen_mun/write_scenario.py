"""Tuen Mun twin, step 4: E's scenario for the IN-26-02615 replay, and a P0-only plans folder.

    python scripts/tuen_mun/write_scenario.py [--label replay-v1] [--leave-share 0.3] [--passing-kmh 25]
    -> sim/scenarios/tuen-mun/evaluator_IN-26-02615_<label>.json
       data/generated-plans/IN-26-02615-p0-only/ (P0.json, generation-inputs.json) on the first run

Everything the closure, drivers' own diversion and the plan routes need is
written from the network here, so a rebuilt network cannot leave a stale edge
in the scenario. The measured inputs behind each number are in
docs/tuen-mun-2026-10-14.md and each scenario's `assumptions`.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

NET = ROOT / "sim/tuen-mun/network.net.xml"
OUT = ROOT / "sim/scenarios/tuen-mun"
PLANS = ROOT / "data/generated-plans/IN-26-02615-p0-only"
BEGIN = "2026-04-15T16:30:00+08:00"
ONSET_S = 4680                  # 17:48:00, the first lane: TDS90033 throughput falls while TDS90032 queues
# lanes shut, from the throughput past the site (TDS90032/33/34, 30-second readings; docs/tuen-mun-2026-10-14.md)
PHASES = [(0, ["fast"]),                       # 17:48  about 3,400 veh/h get by: two lanes
          (660, ["fast", "middle1"]),          # 17:59  about 1,500 veh/h: one lane (TD: "only remaining lane")
          (1740, ["fast"]),                    # 18:17  about 2,950 veh/h: two lanes
          (3180, ["fast", "middle1"])]         # 18:41  0-1,000 veh/h, a near stop: modelled as one lane
CLEARANCE_MIN = 59              # 18:47: all lanes, 4,700 veh/h at TDS90033 from 18:49 (TD CLOSED 18:46)
E = {"scene": "389939170-scene", "approach": "389939170-approach", "upstream": "389939170",
     "leaves_at": "52155204", "sham_tseng_exit": "158584378", "siu_lam_on_ramp": "833525675",
     "tmr_after_siu_lam": "1078219417", "tuen_mun": "1078219416", "siu_lam_local": "1078219421",
     "tmr_from_tsuen_wan": "107646978#1", "ting_kau_bridge_diverge": "1184210830", "route_3_north": "1184210823",
     "tmr_before_ting_kau_exit": "1344086477", "ting_kau_exit": "209559418", "siu_lam_exit": "1078219422"}


def path(net, *waypoints, avoid=()):
    edges = [net.getEdge(waypoints[0])]
    for a, b in zip(waypoints, waypoints[1:]):
        p, _ = net.getShortestPath(net.getEdge(a), net.getEdge(b), vClass="passenger")
        edges += p[1:]
    ids = [e.getID() for e in edges]
    if set(ids) & set(avoid):
        raise RuntimeError(f"path {waypoints} uses {set(ids) & set(avoid)}")
    return ids


def upstream_of(net, edge_id, edges_on):
    """Tuen Mun Road westbound edges from edge_id back to the network's edge, in upstream order."""
    out = [edge_id]
    while True:
        ins = [e for e in net.getEdge(out[-1]).getIncoming() if e.getID() in edges_on]
        if not ins:
            return out
        out.append(ins[0].getID())


def scenario(net, label, leave_share, passing_kmh, length_m, minutes_outside, queue_kmh, routes="sim/tuen-mun/demand_20260415.rou.xml",
             network="sim/tuen-mun/network.net.xml"):
    main = path(net, E["tmr_from_tsuen_wan"], E["tuen_mun"])
    cpr_to_tuen_mun = path(net, E["sham_tseng_exit"], E["siu_lam_on_ramp"], avoid=[E["scene"]])
    # Drivers for Siu Lam end on the exit slip road (sim/tuen-mun/demand_*.json), which Castle Peak Rd
    # cannot reach: plans can advise only drivers for Tuen Mun.
    queue = upstream_of(net, E["approach"], set(main))
    # what a driver at Ting Kau takes for "the queue ahead": Tuen Mun Road at TDS90024/25, before the Sham Tseng
    # exit, where the incident queue arrives at 18:05-18:10; not the Ting Kau merge itself, which slows on
    # ordinary Wednesdays too, nor the exit's own approach
    ting_kau_look = ["157931300#0"]
    return {
        "incident_id": "IN-26-02615",
        "run_prefix": "2026-04-15_TMR",
        "run_label": label,
        "status": ("TUEN MUN BET, INCIDENT REPLAY (14 October, Data). Kept apart from the Aberdeen submission. "
                   "P0 is not yet checked against the detectors; nothing here is a result."),
        "sumo_version": "1.27.1",
        "seed": 2026,
        "inputs": {"network": network, "routes": routes,
                   "detector_loops": "sim/tuen-mun/detectors.add.xml",
                   "observations": "sim/tuen-mun/observations_20260415.json"},
        "run": {"begin": BEGIN, "end_seconds": 14400, "warmup_seconds": 1800, "wall_timeout_seconds": 1800},
        "closure": {
            "edge_id": E["scene"], "lanes_total": 3, "onset_seconds": ONSET_S,
            "phases": [{"offset_seconds": s, "lanes": lanes} for s, lanes in PHASES],
            "reroute_at_edges": [E["upstream"]],
            "scene": {"approach_edges": [E["approach"]], "open_kmh": 80, "passing_kmh": passing_kmh,
                      "crawl_kmh": passing_kmh, "move_over_at_edges": [E["upstream"]],
                      "let_in_after_seconds": 60, "let_in_edges": queue[1:]},
        },
        "vehicles": {"type": "DEFAULT_VEHTYPE", "length_m": length_m},
        "drivers_leave": {
            "share": leave_share, "queue_kmh": queue_kmh, "route_crosses": E["scene"],
            "exits": [{"decide_on": ["1184210836", E["ting_kau_bridge_diverge"]], "exit_edge": E["route_3_north"],
                       "look_ahead": ting_kau_look, "nearside_lanes": 4},
                      {"decide_on": [E["tmr_from_tsuen_wan"], E["tmr_before_ting_kau_exit"]],
                       "exit_edge": E["ting_kau_exit"], "look_ahead": ting_kau_look, "nearside_lanes": 2}],
            "entry": {"edge": E["tmr_from_tsuen_wan"], "after_waiting_seconds": 60},
            "extra_minutes_outside": minutes_outside,
        },
        "plan_actions": {
            "od_groups": {
                "Tsuen Wan & Ting Kau->Tuen Mun": {"via_edge": E["scene"], "to_edge": E["tuen_mun"]},
            },
            "routes": {
                "Castle Peak Road": {"leaves_at": E["leaves_at"], "rejoin": E["tmr_after_siu_lam"],
                                     "with": cpr_to_tuen_mun},
            },
            "signals": {},
        },
        "assumptions": [
            {"choice": "Network: OpenStreetMap geometry, lanes and signal positions; TD Road Network speed limits; "
                       "netconvert's signal timings", "status": "TD publishes no signal timings",
             "source": "sim/tuen-mun/network-audit.md"},
            {"choice": f"Closure phases from TD's lane detectors; onset 17:48, reopening after {CLEARANCE_MIN} min; "
                       "the 18:41-18:47 near stop modelled as one lane open", "status": "measured, one simplification",
             "source": "docs/tuen-mun-2026-10-14.md"},
            {"choice": f"Open lanes pass the scene at {passing_kmh} km/h", "status": "fitted to the throughput past the site",
             "source": "docs/tuen-mun-2026-10-14.md"},
            {"choice": f"Drivers at Ting Kau who see the queue stay on Route 3 with probability {leave_share}, each "
                       f"charged {minutes_outside} min", "status": "share fitted to TDS90024; minutes from TD segment speeds",
             "source": "docs/tuen-mun-2026-10-14.md"},
            {"choice": "Demand: TDS90019 on the day; the Ting Kau merge as on ordinary Wednesdays; Castle Peak Rd from "
                       "the 2024 census; exits at Sham Tseng and Siu Lam fitted on ordinary Wednesdays",
             "status": "observed, census and fitted", "source": "sim/tuen-mun/demand_20260415.json"},
            {"choice": f"Vehicles {length_m} m long on average including buses and lorries",
             "status": "assumption", "source": "docs/tuen-mun-2026-10-14.md"},
        ],
        "metrics": {
            "queue_paths": {"Tuen Mun Road back from the crash site": queue},
            "corridor": {"from_edge": E["tmr_from_tsuen_wan"], "to_edge": E["tuen_mun"], "via_edge": E["scene"]},
            "emergency_route_edges": [E["upstream"], E["approach"]],
            "residential_edge_types": ["highway.residential", "highway.living_street"],
        },
    }


def plans_folder():
    """A do-nothing P0 and its inputs, hand-made from TD's message: the Lead's D workflow replaces them."""
    from src.evaluator.do_nothing_plan import do_nothing
    from src.generation import save_json
    from src.evaluator.od_demand import expected_by_exit
    # modelled demand over the crash site while the plan could act (17:59-18:47), as src/evaluator/od_demand.py
    by_exit = expected_by_exit(ROOT / "sim/tuen-mun/demand_20260415.rou.xml", E["scene"], 5340, 8220)
    incident = {
        "incident_id": "IN-26-02615",
        "source_message_en": ("Due to traffic accident , part of the lanes of Tuen Mun Road (Tuen Mun bound) near "
                              "Hong Kong Garden is closed to all traffic. Only remaining lane is available to "
                              "motorists. Traffic is busy now."),
        "source_message_zh": "因交通意外，屯門公路(往屯門方向)近豪景花園的部份行車線現已封閉。 駕駛人士只可使用餘下行車線行車。 現時上址交通繁忙。", "announced_at": "2026-04-15T17:59:00+08:00", "closed_at": None, "status": "NEW",
        "district": None, "road_name": "Tuen Mun Road", "direction": "Tuen Mun bound",
        "near_landmark": "Hong Kong Garden", "between_landmark": None, "lat": None, "lon": None,
        "coords_source": "none", "incident_type": "traffic_accident", "lanes_closed": ["unspecified"],
        "lanes_total": None, "in_scope": True, "confidence": 0.7,
        "notes": "Transcribed by hand from TD's Special Traffic News for E's P0 run; not a Reader output.",
    }
    context = {
        "incident_id": "IN-26-02615", "reviewed": True,          # Data's draft for P0; the Lead revises it for P1/P2
        "sources": ["docs/tuen-mun-2026-10-14.md", "sim/scenarios/tuen-mun/evaluator_IN-26-02615_replay-v2.json",
                    "sim/tuen-mun/demand_20260415.json", "sim/tuen-mun/network-audit.md"],
        "active_from": "2026-04-15T17:59:00+08:00", "active_until": "2026-04-15T18:47:00+08:00",
        "od_demand_vehicles": {"Tsuen Wan & Ting Kau->Tuen Mun": round(by_exit[E["tuen_mun"]], 1)},
        "routes": [{"od_group": g, "via": v, "roads": [v], "residential": False, "school": True}   # census 2024: major road network, rural road
                   for g, v in (("Tsuen Wan & Ting Kau->Tuen Mun", "Castle Peak Road"),)],
        "blocked_roads": [], "signals": {}, "sign_ids": [], "pt_modes": [],
        "priority_corridor": {"od": "Tuen Mun Road->crash site", "keep_clear": ["Tuen Mun Road"]},
    }
    p0 = do_nothing(incident, context)
    PLANS.mkdir(parents=True, exist_ok=True)
    save_json(PLANS / "generation-inputs.json", {"incident": incident, "policy_context": context})
    save_json(PLANS / "P0.json", p0)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", default="replay-v1")
    parser.add_argument("--leave-share", type=float, default=0.2)
    parser.add_argument("--passing-kmh", type=float, default=30)
    parser.add_argument("--length-m", type=float, default=7.0)
    parser.add_argument("--minutes-outside", type=float, default=4)
    parser.add_argument("--queue-kmh", type=float, default=15)
    parser.add_argument("--routes", default="sim/tuen-mun/demand_20260415.rou.xml")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--network", default="sim/tuen-mun/network.net.xml",
                        help="sim/tuen-mun/network-fixed-time.net.xml for the fixed-time signal sensitivity")
    args = parser.parse_args()
    import sumolib
    net = sumolib.net.readNet(str(NET))
    OUT.mkdir(parents=True, exist_ok=True)
    doc = scenario(net, args.label, args.leave_share, args.passing_kmh, args.length_m, args.minutes_outside,
                   args.queue_kmh, args.routes, args.network)
    doc["seed"] = args.seed
    path_out = OUT / f"evaluator_IN-26-02615_{args.label}.json"
    path_out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    if not (PLANS / "P0.json").exists():
        plans_folder()
    print(path_out, file=sys.stderr)


if __name__ == "__main__":
    main()
