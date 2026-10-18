"""Provenance-bound map geometry for the frozen Tuen Mun P2 detour."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.console import road_geometry


INCIDENT_ID = "IN-26-02615"
NETWORK = Path("sim/tuen-mun/network.net.xml")
SCENARIOS = Path("sim/scenarios/tuen-mun")
OBSERVATIONS = Path("sim/tuen-mun/observations_20260415.json")
ROUTE_COLOUR = [214, 48, 194, 245]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root: Path, results_dir: Path, p2_run: dict) -> dict:
    """Return road paths only when the selected run's recorded inputs match.

    The provenance sidecar identifies the exact network and scenario used by
    the saved evaluator run. Never infer a route from a plan label alone.
    """
    if p2_run.get("incident_id") != INCIDENT_ID or p2_run.get("plan_id") != "P2":
        raise ValueError("Selected run is not Tuen Mun P2.")
    run_id = p2_run["run_id"]
    provenance = json.loads((results_dir / f"{run_id}.provenance.json").read_text())
    if provenance.get("run_id") != run_id or provenance.get("plan_id") != "P2":
        raise ValueError("Run provenance does not match the selected P2 result.")
    inputs = provenance["simulation_inputs"]
    network = root / NETWORK
    if _sha(network) != inputs["network"]:
        raise ValueError("Tuen Mun network differs from the evaluated run.")
    observations_path = root / OBSERVATIONS
    if _sha(observations_path) != inputs["observations"]:
        raise ValueError("Tuen Mun observations differ from the evaluated run.")
    observations = json.loads(observations_path.read_text())
    scenario_path = next(
        (path for path in sorted((root / SCENARIOS).glob("*.json"))
         if _sha(path) == inputs["scenario"]), None)
    if scenario_path is None:
        raise ValueError("The evaluated Tuen Mun scenario is unavailable.")
    scenario = json.loads(scenario_path.read_text())
    edge_ids = scenario["plan_actions"]["routes"]["Castle Peak Road"]["with"]
    geometry = road_geometry.load_geometry(network, inputs["network"])
    route = road_geometry.route_geometry(geometry, edge_ids, inputs["network"])
    route = [{**path, "colour": ROUTE_COLOUR, "width": 8,
              "tooltip": "P2 tested Castle Peak Road detour · simulated candidate"}
             for path in route]

    roads_by_id = {road["edge_id"]: road for road in geometry["roads"]}
    nodes = []
    for index, label in ((0, "Sham Tseng"), (8, "Castle Peak Road"),
                         (17, "Tsing Lung Tau"), (27, "Tai Lam"),
                         (len(edge_ids) - 1, "Siu Lam rejoin")):
        nodes.append({"position": roads_by_id[edge_ids[index]]["path"][-1],
                      "tooltip": f"Road-network junction · {label}",
                      "label": label, "colour": [255, 255, 255, 255]})
    crash_edge = scenario["closure"]["edge_id"]
    crash = roads_by_id[crash_edge]["path"]
    nodes.append({"position": crash[len(crash) // 2],
                  "tooltip": "Modelled crash site on Tuen Mun Road",
                  "label": "Crash", "colour": [226, 104, 91, 255]})

    detectors = observations["detectors"]
    route_points = [p for item in route for p in item["path"]]
    all_points = [*route_points, *([d["lon"], d["lat"]] for d in detectors)]
    west = min(p[0] for p in all_points)
    east = max(p[0] for p in all_points)
    south = min(p[1] for p in all_points)
    north = max(p[1] for p in all_points)
    padding = 0.004
    context = [road for road in geometry["roads"]
               if any(west - padding <= p[0] <= east + padding
                      and south - padding <= p[1] <= north + padding
                      for p in road["path"])]
    context = [{**road, "colour": [75, 107, 122, 145], "width": 2}
               for road in context]
    times = [bin_["time"] for bin_ in detectors[0]["observations"]]
    return {"roads": context, "route": route, "nodes": nodes,
            "detectors": detectors, "times": times,
            "bounds": (west, south, east, north),
            "network_sha256": inputs["network"], "scenario_sha256": inputs["scenario"],
            "observations_sha256": inputs["observations"]}


def detector_points(detectors: list[dict], time: str) -> list[dict]:
    """Colour real TD detector readings for one archived five-minute bin."""
    points = []
    for detector in detectors:
        reading = next((item for item in detector["observations"]
                        if item["time"] == time), None)
        if reading is None:
            raise ValueError(f"Detector {detector['id']} lacks {time}.")
        speed = reading["speed_kmh"]
        if speed is None:
            colour, speed_label = [150, 160, 169, 255], "No speed reading"
        elif speed < 30:
            colour, speed_label = [225, 69, 76, 255], f"{speed:g} km/h"
        elif speed < 60:
            colour, speed_label = [239, 136, 47, 255], f"{speed:g} km/h"
        else:
            colour, speed_label = [16, 170, 178, 255], f"{speed:g} km/h"
        count = reading["count"]
        count_label = f"{count} vehicles" if count is not None else "Count withheld/unavailable"
        points.append({"position": [detector["lon"], detector["lat"]],
                       "colour": colour, "id": detector["id"],
                       "tooltip": f"TD roadside detector {detector['id']}\n"
                                  f"{time[11:16]} HKT · {speed_label}\n{count_label}"})
    return points
