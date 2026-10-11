"""Read actual SUMO road shapes for an optional map-alignment preview.

This is geometry only: it neither selects routes nor claims a plan is feasible.
Keep each directed edge separate so unrelated roads are never joined by a line.
"""
from __future__ import annotations

import hashlib
import html
import math
import re
from pathlib import Path

import sumolib

# Visual grouping from docs/02-data.md section 5, not approved diversion plans.
ROAD_GROUPS = {
    "Main corridor": {"aberdeen praya road", "wong chuk hang road",
                      "wong chuk hang road flyover", "aberdeen tunnel",
                      "wong nai chung gap flyover", "canal road flyover"},
    "Alternative roads": {"pok fu lam road", "shek pai wan road",
                          "wong nai chung gap road", "stubbs road"},
}
COLOURS = {"Main corridor": [40, 100, 220, 220],
           "Alternative roads": [133, 72, 184, 220],
           "Other roads": [110, 125, 140, 150]}


def road_group(name: str) -> str:
    """Match the full English name, so Old Pok Fu Lam Road is not conflated."""
    english = re.search(r"[A-Za-z][A-Za-z '’./-]*$", name)
    normalized = english.group().strip().casefold() if english else ""
    return next((group for group, names in ROAD_GROUPS.items() if normalized in names),
                "Other roads")


def _geographic_shape(net, shape) -> list[list[float]]:
    points = [list(net.convertXY2LonLat(x, y)) for x, y in shape]
    if any(not math.isfinite(lon) or not math.isfinite(lat)
           or not -180 <= lon <= 180 or not -90 <= lat <= 90
           for lon, lat in points):
        raise ValueError("Network contains invalid geographic coordinates.")
    return points


def _connection_lanes(net, connection):
    """Follow only the internal lanes explicitly attached to this turn."""
    pending = [connection.getViaLaneID()]
    seen = set()
    while pending:
        lane_id = pending.pop()
        if not lane_id or lane_id in seen:
            continue
        seen.add(lane_id)
        lane = net.getLane(lane_id)
        if not lane.allows("passenger"):
            continue
        yield lane
        # Some turns use several internal lanes around an internal junction.
        for onward in lane.getOutgoing():
            if (onward.getToLane() == connection.getToLane()
                    and onward.allows("passenger")):
                pending.append(onward.getViaLaneID())


def select_geometry(geometry: dict, view: str, road_name: str | None = None) -> list[dict]:
    """Select real edge shapes and only their connecting junction geometry."""
    roads = geometry["roads"]
    if view == "Corridor network":
        roads = [r for r in roads if r["group"] in ROAD_GROUPS]
    elif view == "Single road":
        roads = [r for r in roads if r["road_name"] == road_name]
    elif view != "Full supplied network":
        raise ValueError(f"Unknown map view: {view}")
    ids = {r["edge_id"] for r in roads}
    junctions = [j for j in geometry["junctions"]
                 if j["from_edge"] in ids and j["to_edge"] in ids]
    return [*roads, *junctions]


def route_geometry(geometry: dict, edge_ids: list[str], network_sha256: str) -> list[dict]:
    """Preview an ordered route using only edges and turns in one SUMO network.

    A route must come from a reviewed scenario; this function neither chooses
    the route nor infers a missing connection. It does not verify run provenance.
    """
    if network_sha256 != geometry["network_sha256"]:
        raise ValueError("Route and displayed network have different identities.")
    if not edge_ids:
        raise ValueError("Route has no SUMO edges.")
    roads = {road["edge_id"]: road for road in geometry["roads"]}
    unknown = [edge_id for edge_id in edge_ids if edge_id not in roads]
    if unknown:
        raise ValueError(f"Route contains unknown or inaccessible edge: {unknown[0]}")

    junctions = {lane["lane_id"]: lane for lane in geometry["junctions"]}
    turns = {}
    for connection in geometry["connections"]:
        key = (connection["from_edge"], connection["to_edge"])
        turns.setdefault(key, []).append(connection["via_lane_ids"])

    # Validate the entire edge sequence before returning any overlay.
    chosen_turns = []
    for start, end in zip(edge_ids, edge_ids[1:]):
        choices = turns.get((start, end), [])
        if not choices:
            raise ValueError(f"No passenger-vehicle connection from {start} to {end}.")
        chosen_turns.append(min(choices))  # deterministic legal turn geometry

    paths = []
    for index, edge_id in enumerate(edge_ids):
        paths.append(roads[edge_id])
        if index < len(chosen_turns):
            paths.extend(junctions[lane_id] for lane_id in chosen_turns[index])
    return paths


def load_geometry(path: Path, expected_sha256: str) -> dict:
    """Convert a specific network's carriageway centres into WGS84 paths."""
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("Network changed; reload the preview.")
    net = sumolib.net.readNet(str(path), withInternal=True)
    if not net.hasGeoProj():
        raise ValueError("Network has no geographic projection; cannot align it to the map.")
    roads, edges = [], {}
    for edge in net.getEdges():
        if edge.getFunction() or not edge.allows("passenger"):
            continue
        # No includeJunctions: that option extends to node centres, not the
        # actual turn geometry. Do not draw invented connectors across gaps.
        shape = edge.getShape()
        if len(shape) < 2:
            continue
        points = _geographic_shape(net, shape)
        name = html.unescape(edge.getName()) or "Unnamed road"
        group = road_group(name)
        edges[edge.getID()] = edge
        roads.append({"edge_id": edge.getID(), "road_name": name,
                      "path": points, "group": group, "colour": COLOURS[group],
                      "width": 3 if group in ROAD_GROUPS else 1,
                      "kind": "road",
                      "tooltip": f"{name}\nSUMO edge {edge.getID()}\n"
                                 "Geometry preview · not route advice"})
    if not roads:
        raise ValueError("Network contains no drawable passenger-road geometry.")
    junctions = {}
    route_connections = []
    for edge in edges.values():
        for target, outgoing in edge.getOutgoing().items():
            if target.getID() not in edges:
                continue
            for connection in outgoing:
                if not (connection.allows("passenger")
                        and connection.getFromLane().allows("passenger")
                        and connection.getToLane().allows("passenger")):
                    continue
                via_lanes = list(_connection_lanes(net, connection))
                route_connections.append({"from_edge": edge.getID(),
                                          "to_edge": target.getID(),
                                          "via_lane_ids": tuple(lane.getID()
                                                                for lane in via_lanes
                                                                if len(lane.getShape()) >= 2)})
                for lane in via_lanes:
                    if len(lane.getShape()) < 2:
                        continue
                    key = (edge.getID(), target.getID(), lane.getID())
                    group = road_group(html.unescape(edge.getName()))
                    junctions[key] = {
                        "from_edge": edge.getID(), "to_edge": target.getID(),
                        "lane_id": lane.getID(), "kind": "junction",
                        "group": group, "colour": COLOURS[group],
                        "width": 3 if group in ROAD_GROUPS else 1,
                        "path": _geographic_shape(net, lane.getShape()),
                        "tooltip": f"SUMO junction lane {lane.getID()}\n"
                                   "Network connection · not route advice",
                    }
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("Network changed while loading; reload the preview.")
    return {"network_sha256": expected_sha256, "roads": roads,
            "junctions": list(junctions.values()),
            "connections": route_connections}
