"""Tuen Mun twin, step 3: observed demand, 16:30-20:30, in 15-minute flows.

    python scripts/tuen_mun/demand.py --day 2026-04-15      (the incident day)
    python scripts/tuen_mun/demand.py --day 2026-04-22      (an ordinary Wednesday, for calibration)
    -> sim/tuen-mun/demand_<day>.rou.xml and demand_<day>.json (every number and where it came from)

Where traffic comes from:

  Tuen Mun Road from Tsuen Wan   that day's TDS90019 count (TDS90017, TDS90020 where 19 is missing).
                                 The queue never reached TDS90019, so this is what arrived, already
                                 net of drivers who avoided Tuen Mun Road before reaching it.
  Ting Kau Bridge (Route 3) slip the ordinary-day mean of TDS90024 minus TDS90019: what joins at
                                 Ting Kau on a Wednesday. On the incident day some of these drivers
                                 stay on Route 3 instead; E's drivers_leave rule does that (scenario).
  Castle Peak Road westbound     Annual Traffic Census 2024 station 6209 (Castle Peak Rd between Tuen
                                 Mun Rd and Sham Tseng): weekday AADT x its weekday hourly profile x the
                                 westbound share of its PM peak hour. On the incident day, plus the
                                 drivers missing at TDS90019 against ordinary days: they reached Tuen
                                 Mun some other way, and Siu Lam took 500-750 more than usual
                                 (docs/tuen-mun-2026-10-14.md).
  Castle Peak Road eastbound     census station 5657 (Sham Tseng to Siu Lam) the same way.

Where it goes, as shares fitted on the three ordinary Wednesdays:

  Sham Tseng exit     1 - TDS90029/TDS90025 (12.2% on each of the three days); some of these go
                      on along Castle Peak Road westbound, enough to make census 5657's westbound flow
  Siu Lam exit        what TDS90039 is short of TDS90033 once Castle Peak Road traffic rejoining at
                      Siu Lam is counted in; these drivers end on the exit slip road, since their
                      destinations are local (Siu Lam, So Kwun Wat, Gold Coast) and OSM's Siu Lam
                      Interchange has the exit and the Castle Peak Rd on-slip crossing on one
                      single-lane link, which netconvert's equal-priority junctions deadlock
  the rest            Tuen Mun Road west, past TDS90043
"""
import argparse
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.loaders import detectors   # noqa: E402

NET = ROOT / "sim/tuen-mun/network.net.xml"
OUT = ROOT / "sim/tuen-mun"
HK = dt.timezone(dt.timedelta(hours=8))
BEGIN, END, BIN_MIN = "16:30", "20:30", 15
ORDINARY = ["2026-04-22", "2026-04-29", "2026-05-06"]
INCIDENT_DAY = "2026-04-15"

EDGES = {
    "tmr_from_tsuen_wan": "107646978#1", "ting_kau_bridge": "1184210836", "cpr_from_tsuen_wan": "757290378",
    "cpr_from_so_kwun_wat": "102290333",
    "tuen_mun": "1078219416", "sham_tseng_exit": "158584378", "sham_tseng_local": "452269559",
    "siu_lam_exit": "1078219422", "so_kwun_wat": "829563400", "siu_lam_local": "1078219421", "siu_lam_on_ramp": "833525675",
    "cpr_to_tsuen_wan": "173395446", "cpr_sham_tseng_eastbound": "158584310",
    "tmr_ting_kau_merge": "1344086465",
}
# Annual Traffic Census 2024 (data/tuen-mun/census/): station 6209 Castle Peak Rd - Tsuen Wan, Ting Kau & Sham Tseng
# (Tuen Mun Rd -> Sham Tseng); station 5657 Castle Peak Rd - Sham Tseng, Tsing Lung Tau & Tai Lam (Sham Tseng -> Siu Lam)
CENSUS = {
    "6209": {"aadt_weekday_two_way": 4110 + 4570, "pm_peak_westbound": 460, "pm_peak_eastbound": 230},
    "5657": {"aadt_two_way": 13480},
    # S6209.xls, weekday share of the day's two-way flow in each hour (hour starting 16..20)
    "weekday_hourly_pct": {16: 5.824689, 17: 6.520005, 18: 8.001823, 19: 7.101334, 20: 5.243361},
}
WESTBOUND_SHARE = CENSUS["6209"]["pm_peak_westbound"] / (CENSUS["6209"]["pm_peak_westbound"]
                                                         + CENSUS["6209"]["pm_peak_eastbound"])
WEEKDAY_FACTOR = CENSUS["6209"]["aadt_weekday_two_way"] / 8780          # 6209: weekday / all-day AADT
CPR_REJOIN_SHARE = 0.5           # assumption: half of Castle Peak Rd westbound through traffic rejoins at Siu Lam
EXTRA_WINDOW = ("17:45", "19:30")
# Drivers who would have joined at Ting Kau but decided before getting there (TD's message, radio, apps): the net
# loss at Ting Kau over 17:30-20:30 is TDS90024's shortfall less TDS90019's (1,888 - 447 = 1,441 vehicles), of
# which Route 3 northbound at the Tai Lam Tunnel (AID03115/16) gained only about 300, the drivers who stay on
# Route 3 at Ting Kau itself (E's drivers_leave). The rest never reach the model on 15 Apr.
TING_KAU_DECIDED_EARLIER = 1441 - 300
TING_KAU_WINDOW = ("18:00", "19:30")     # from TD's 17:59 message until the queue at Ting Kau cleared
STARTUP_S = 0.0                     # SUMO's default until the queue-discharge fit
TAU_S = 1.0                         # SUMO's default headway until the queue-discharge fit (docs/tuen-mun-2026-10-14.md)   # from the first slowing at TDS90031 to the end of the queue at TDS90021-25


def slots(day):
    start = dt.datetime.fromisoformat(f"{day}T{BEGIN}").replace(tzinfo=HK)
    end = dt.datetime.fromisoformat(f"{day}T{END}").replace(tzinfo=HK)
    return start, end, detectors.slot_starts(start, end, BIN_MIN)


def counts(day, ids):
    """Vehicles per 15-minute bin at each detector, from the flow rate over the observed seconds."""
    start, end, _ = slots(day)
    rows = detectors.load_window(start, end, ids, log=lambda *a: None)
    out = {d: {} for d in ids}
    for b in detectors.bin_window(rows, BIN_MIN, start=start, end=end, detector_ids=ids):
        if b["flow_veh_h"] not in (None, "") and b["coverage_pct"] >= 20:
            out[b["detector_id"]][b["bin_start"][11:16]] = float(b["flow_veh_h"]) * BIN_MIN / 60
    return out


def first_available(c, ids, t):
    for d in ids:
        if t in c[d]:
            return c[d][t], d
    return None, None


def census_cpr(t, station_two_way, direction_share):
    hour = int(t[:2])
    return station_two_way * WEEKDAY_FACTOR * CENSUS["weekday_hourly_pct"][hour] / 100 * direction_share \
        * BIN_MIN / 60


def build(day):
    ids = ["TDS90017", "TDS90019", "TDS90020", "TDS90024", "TDS90025", "TDS90029", "TDS90031", "TDS90033",
           "TDS90039", "TDS90040", "TDS90041"]
    _, _, starts = slots(day)
    times = [s.strftime("%H:%M") for s in starts]
    today = counts(day, ids)
    ordinary = {d: counts(d, ids) for d in ORDINARY}

    def ordinary_mean(detector_ids, t):
        vals = [first_available(ordinary[d], detector_ids, t)[0] for d in ORDINARY]
        vals = [v for v in vals if v is not None]
        return statistics.mean(vals) if vals else None

    rows = []
    for t in times:
        tmr, source = first_available(today, ["TDS90019", "TDS90017", "TDS90020"], t)
        merge = ordinary_mean(["TDS90024", "TDS90025"], t) - ordinary_mean(["TDS90019", "TDS90017"], t)
        cpr_wb = census_cpr(t, CENSUS["6209"]["aadt_weekday_two_way"] / WEEKDAY_FACTOR, WESTBOUND_SHARE)
        cpr_wb_5657 = census_cpr(t, CENSUS["5657"]["aadt_two_way"], WESTBOUND_SHARE)
        cpr_eb_5657 = census_cpr(t, CENSUS["5657"]["aadt_two_way"], 1 - WESTBOUND_SHARE)
        cpr_eb_6209 = census_cpr(t, CENSUS["6209"]["aadt_weekday_two_way"] / WEEKDAY_FACTOR, 1 - WESTBOUND_SHARE)
        rows.append({"bin": t, "tuen_mun_road_from_tsuen_wan": tmr, "counted_at": source,
                     "tuen_mun_road_from_tsuen_wan_ordinary": ordinary_mean(["TDS90019", "TDS90017", "TDS90020"], t),
                     "ting_kau_merge_ordinary": merge, "castle_peak_road_westbound": cpr_wb,
                     "castle_peak_road_westbound_extra": 0.0, "castle_peak_road_westbound_at_tsing_lung_tau": cpr_wb_5657,
                     "castle_peak_road_eastbound_at_tsing_lung_tau": cpr_eb_5657,
                     "castle_peak_road_eastbound_to_tsuen_wan": cpr_eb_6209})
    if day == INCIDENT_DAY:
        # Drivers missing at TDS90019 while the incident lasted (17:45-19:30) against the ordinary mean: they
        # reached Tuen Mun another way; Castle Peak Rd from Tsuen Wan is the one modelled. Net over the window,
        # spread in proportion to ordinary flow, so day-to-day noise in single bins does not add vehicles.
        during = [r for r in rows if EXTRA_WINDOW[0] <= r["bin"] < EXTRA_WINDOW[1]]
        missing = sum(r["tuen_mun_road_from_tsuen_wan_ordinary"] - r["tuen_mun_road_from_tsuen_wan"] for r in during)
        usual = sum(r["tuen_mun_road_from_tsuen_wan_ordinary"] for r in during)
        for r in during:
            r["castle_peak_road_westbound_extra"] = max(0.0, missing) * r["tuen_mun_road_from_tsuen_wan_ordinary"] / usual
        window = [r for r in rows if TING_KAU_WINDOW[0] <= r["bin"] < TING_KAU_WINDOW[1]]
        merge_total = sum(r["ting_kau_merge_ordinary"] for r in window)
        for r in rows:
            r["ting_kau_decided_earlier"] = (TING_KAU_DECIDED_EARLIER * r["ting_kau_merge_ordinary"] / merge_total
                                             if r in window else 0.0)

    # shares, from the three ordinary Wednesdays over the whole window
    def total(c, d):
        return sum(c[d].get(t, 0) for t in times if all(t in c[x] for x in ("TDS90025", "TDS90029", "TDS90033", "TDS90039")))
    sham_tseng = statistics.mean(1 - total(ordinary[d], "TDS90029") / total(ordinary[d], "TDS90025") for d in ORDINARY)
    flow_at_25 = sum(r["tuen_mun_road_from_tsuen_wan"] + r["ting_kau_merge_ordinary"] for r in rows)
    exit_volume = sham_tseng * flow_at_25
    st_on_along_cpr = max(0.0, (sum(r["castle_peak_road_westbound_at_tsing_lung_tau"] for r in rows)
                                - sum(r["castle_peak_road_westbound"] for r in rows)) / exit_volume)
    rejoin = CPR_REJOIN_SHARE * sum(r["castle_peak_road_westbound_at_tsing_lung_tau"] for r in rows)
    ratio_39_33 = statistics.mean(total(ordinary[d], "TDS90039") / total(ordinary[d], "TDS90033") for d in ORDINARY)
    at_33 = flow_at_25 * (1 - sham_tseng)
    siu_lam = 1 - (ratio_39_33 * at_33 - rejoin) / at_33
    shares = {"sham_tseng_exit": round(sham_tseng, 4), "of_them_on_along_castle_peak_road": round(st_on_along_cpr, 4),
              "siu_lam_exit": round(siu_lam, 4), "castle_peak_road_through_traffic_rejoining_at_siu_lam": CPR_REJOIN_SHARE,
              "ordinary_ratio_TDS90039_to_TDS90033": round(ratio_39_33, 4)}
    return rows, shares


def write_routes(day, rows, shares, tau=1.0, suffix="", startup=0.0):
    import sumolib
    net = sumolib.net.readNet(str(NET))

    def path(*waypoints):
        edges = [net.getEdge(waypoints[0])]
        for a, b in zip(waypoints, waypoints[1:]):
            p, _ = net.getShortestPath(net.getEdge(a), net.getEdge(b), vClass="passenger")
            if p is None:
                raise RuntimeError(f"no path {a} -> {b}")
            edges += p[1:]
        return " ".join(e.getID() for e in edges)

    E = EDGES
    routes = {
        "tmr_to_tuen_mun": path(E["tmr_from_tsuen_wan"], E["tuen_mun"]),
        "tmr_to_siu_lam": path(E["tmr_from_tsuen_wan"], E["siu_lam_exit"], E["siu_lam_local"]),
        "tmr_to_sham_tseng": path(E["tmr_from_tsuen_wan"], E["sham_tseng_exit"], E["sham_tseng_local"]),
        "tmr_to_sham_tseng_then_cpr": path(E["tmr_from_tsuen_wan"], E["sham_tseng_exit"], E["so_kwun_wat"]),
        "tkb_to_tuen_mun": path(E["ting_kau_bridge"], E["tmr_ting_kau_merge"], E["tuen_mun"]),
        "tkb_to_siu_lam": path(E["ting_kau_bridge"], E["tmr_ting_kau_merge"], E["siu_lam_exit"], E["siu_lam_local"]),
        "tkb_to_sham_tseng": path(E["ting_kau_bridge"], E["tmr_ting_kau_merge"], E["sham_tseng_exit"], E["sham_tseng_local"]),
        "tkb_to_sham_tseng_then_cpr": path(E["ting_kau_bridge"], E["tmr_ting_kau_merge"], E["sham_tseng_exit"], E["so_kwun_wat"]),
        "cpr_to_tuen_mun": path(E["cpr_from_tsuen_wan"], E["siu_lam_on_ramp"], E["tuen_mun"]),
        "cpr_to_so_kwun_wat": path(E["cpr_from_tsuen_wan"], E["so_kwun_wat"]),
        "cpr_eastbound_to_tsuen_wan": path(E["cpr_from_so_kwun_wat"], E["cpr_to_tsuen_wan"]),
        "cpr_eastbound_to_sham_tseng": path(E["cpr_from_so_kwun_wat"], E["cpr_sham_tseng_eastbound"]),
    }
    for name, edges in routes.items():
        if "1078219416" in edges.split() and "389939170-scene" not in edges.split() and name.startswith(("tmr", "tkb")):
            raise RuntimeError(f"{name} does not pass the crash site")
    st, on, sl = shares["sham_tseng_exit"], shares["of_them_on_along_castle_peak_road"], shares["siu_lam_exit"]
    split = {"to_tuen_mun": (1 - st) * (1 - sl), "to_siu_lam": (1 - st) * sl,
             "to_sham_tseng": st * (1 - on), "to_sham_tseng_then_cpr": st * on}
    lines = ["<?xml version='1.0' encoding='utf-8'?>",
             f"<!-- Observed demand for {day}, 16:30-20:30: scripts/tuen_mun/demand.py (demand_{day}.json) -->",
             "<routes>",
             f'  <vType id="DEFAULT_VEHTYPE" vClass="passenger" length="5" speedFactor="1" speedDev="0.05" sigma="0" tau="{tau}" startupDelay="{startup}"/>']
    flows = []
    for i, r in enumerate(rows):
        begin, end = i * BIN_MIN * 60, (i + 1) * BIN_MIN * 60
        tkb = r["ting_kau_merge_ordinary"] - r.get("ting_kau_decided_earlier", 0.0)
        groups = [("tmr", r["tuen_mun_road_from_tsuen_wan"]), ("tkb", tkb)]
        for origin, volume in groups:
            for dest, share in split.items():
                flows.append((begin, end, f"{origin}_{dest}", volume * share))
        flows.append((begin, end, "cpr_to_tuen_mun", r["castle_peak_road_westbound_extra"]
                      + r["castle_peak_road_westbound"] * shares["castle_peak_road_through_traffic_rejoining_at_siu_lam"]))
        flows.append((begin, end, "cpr_to_so_kwun_wat", r["castle_peak_road_westbound"]
                      * (1 - shares["castle_peak_road_through_traffic_rejoining_at_siu_lam"])))
        flows.append((begin, end, "cpr_eastbound_to_tsuen_wan", r["castle_peak_road_eastbound_to_tsuen_wan"]))
        flows.append((begin, end, "cpr_eastbound_to_sham_tseng",
                      max(0.0, r["castle_peak_road_eastbound_at_tsing_lung_tau"] - r["castle_peak_road_eastbound_to_tsuen_wan"])))
    carried, written = {}, 0          # whole vehicles per bin, carrying each route's remainder to its next bin
    for begin, end, route, volume in sorted(flows, key=lambda f: (f[0], f[2])):
        due = carried.get(route, 0.0) + volume
        n = int(due + 0.5)
        carried[route] = due - n
        if n > 0:
            written += n
            lines.append(f'  <flow id="{route}.{begin // 60:03d}" type="DEFAULT_VEHTYPE" begin="{begin}" end="{end}" '
                         f'number="{n}" departLane="best" departSpeed="max"><route edges="{routes[route]}"/></flow>')
    lines.append("</routes>")
    tag = day.replace("-", "")
    (OUT / f"demand_{tag}{suffix}.rou.xml").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    (OUT / f"demand_{tag}{suffix}.json").write_text(json.dumps({"day": day, "window": [BEGIN, END], "bin_minutes": BIN_MIN,
                                                         "shares": shares, "split": split, "census": CENSUS,
                                                         "westbound_share_castle_peak_road": WESTBOUND_SHARE,
                                                         "bins": rows, "routes": routes}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(day, "vehicles", written, "shares", shares, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--day", required=True)
    parser.add_argument("--tau", type=float, default=TAU_S, help="drivers' desired time headway, s")
    parser.add_argument("--startup-delay", type=float, default=STARTUP_S, help="s a driver takes to move off from a stop")
    parser.add_argument("--suffix", default="", help="written as demand_<day><suffix>.rou.xml, for calibration variants")
    args = parser.parse_args()
    rows, shares = build(args.day)
    write_routes(args.day, rows, shares, args.tau, args.suffix, args.startup_delay)


if __name__ == "__main__":
    main()
