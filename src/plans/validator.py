"""Reject unsafe or unsupported proposals before E receives them.

Route exposure and OD demand are supplied by C/E, never inferred by the LLM.
Residential routes are conservatively counted as entirely residential.
"""
from copy import deepcopy
from datetime import datetime, time, timedelta, timezone

from src.generation import validate
from src.plans.schema import CONTEXT_SCHEMA, PLAN_SCHEMA

HK = timezone(timedelta(hours=8))
CHECKS = ["residential_share_under_15pct", "no_school_street_peak",
          "emergency_corridor_clear", "od_shares_at_most_one", "no_blocked_road"]
RESIDENTIAL_LIMIT = 0.15


def key(value):
    return " ".join(value.casefold().split())


def school_peak(start, end):
    """Does any part of the half-open action window overlap a school peak?"""
    day = start.date()
    while day <= end.date():
        for a, b in ((time(7, 30), time(8, 30)), (time(15), time(16))):
            if start < datetime.combine(day, b, HK) and end > datetime.combine(day, a, HK):
                return True
        day += timedelta(days=1)
    return False


def validate_context(context, incident):
    validate(context, CONTEXT_SCHEMA)
    if context["incident_id"] != incident["incident_id"]:
        raise ValueError("Policy context belongs to a different incident")
    start = datetime.fromisoformat(context["active_from"]).astimezone(HK)
    end = datetime.fromisoformat(context["active_until"]).astimezone(HK)
    announced = datetime.fromisoformat(incident["announced_at"])
    if announced.utcoffset() is None or start < announced or start >= end:
        raise ValueError("Action window must start at/after the report and end after its start")
    seen = set()
    for route in context["routes"]:
        pair = (route["od_group"], key(route["via"]))
        if pair in seen or route["od_group"] not in context["od_demand_vehicles"]:
            raise ValueError("Duplicate route or route without OD demand")
        if key(route["via"]) not in {key(r) for r in route["roads"]}:
            raise ValueError("Route roads must include its via road")
        seen.add(pair)
    if sum(context["od_demand_vehicles"].values()) <= 0:
        raise ValueError("Positive OD demand is required for the residential share check")
    return start, end


def validate_plan(plan, context, incident):
    validate(plan, PLAN_SCHEMA)
    start, end = validate_context(context, incident)
    result = deepcopy(plan)
    if plan["priority_corridor"] != context["priority_corridor"]:
        raise ValueError("A proposal cannot replace the reviewed emergency priority corridor")
    protected = {key(r) for r in context["priority_corridor"]["keep_clear"]}
    blocked = {key(r) for r in context["blocked_roads"]}
    if incident["lanes_closed"] and incident["road_name"]:
        blocked.add(key(incident["road_name"]))
    routes = {(r["od_group"], key(r["via"])): r for r in context["routes"]}
    shares, pairs, diverted, residential = {}, set(), 0.0, 0.0
    for diversion in plan["diversions"]:
        od, via, share = diversion["od_group"], key(diversion["via"]), diversion["share"]
        pair = (od, via)
        if pair not in routes or pair in pairs:
            raise ValueError("Unknown or duplicate OD/route diversion")
        pairs.add(pair)
        route = routes[pair]
        roads = {key(r) for r in route["roads"]}
        if roads & blocked:
            raise ValueError("Diversion crosses a blocked road")
        if roads & protected:
            raise ValueError("Diversion crosses the emergency priority corridor")
        if route["school"] and school_peak(start, end):
            raise ValueError("School route diversion overlaps a school peak")
        shares[od] = shares.get(od, 0) + share
        vehicles = context["od_demand_vehicles"][od] * share
        diverted += vehicles
        residential += vehicles if route["residential"] else 0
    if any(share > 1 + 1e-9 for share in shares.values()):
        raise ValueError("Diversion shares for an OD group exceed one")
    if diverted and residential / diverted > RESIDENTIAL_LIMIT + 1e-9:
        raise ValueError("Residential share of diverted demand exceeds 15%")
    seen_signals = set()
    for signal in plan["signals"]:
        junction = signal["junction_id"]
        if (junction not in context["signals"] or junction in seen_signals
                or signal["green_extend_s"] > context["signals"][junction]):
            raise ValueError("Unknown, duplicate or excessive signal extension")
        seen_signals.add(junction)
    signs = [v["sign_id"] for v in plan["vms"]]
    if len(set(signs)) != len(signs) or not set(signs) <= set(context["sign_ids"]):
        raise ValueError("Unknown or duplicate VMS sign")
    pt = plan["pt_nudge"]
    if bool(pt["mode"]) != bool(pt["intent"]) or (pt["mode"] and pt["mode"] not in context["pt_modes"]):
        raise ValueError("Unsupported public transport nudge")
    if plan["plan_id"] == "P0":
        if plan["diversions"] or plan["signals"] or plan["vms"] or pt["mode"]:
            raise ValueError("P0 must contain no intervention")
    if plan["plan_id"] == "P1":
        if (not plan["diversions"] or len({key(d["via"]) for d in plan["diversions"]}) != 1
                or set(shares) != set(context["od_demand_vehicles"])
                or any(d["share"] != 1 for d in plan["diversions"])
                or plan["signals"] or pt["mode"]):
            raise ValueError("P1 must broadcast one detour to all supplied OD groups")
    result["constraints_checked"] = CHECKS.copy()
    return result
