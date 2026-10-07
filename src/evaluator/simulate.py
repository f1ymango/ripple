"""Run SUMO once with the scenario's lane closure. No plan logic lives here.

Without a scene the closure is injected the way Simulation's
src/twin/run_scenario.py does it: the closed lanes' speed limit is set to zero
for the closure and restored at reopening, so vehicles queue rather than lose
their route. With a scene (scenario.py) E also sets the speeds around the
crash, and a lane closed beside an open one is closed to traffic instead.

Anything else that acts during the run is a controller: an object with
`step(traci, now)`, called once a second before SUMO moves. Drivers leaving at
exits (behaviour.py) and a plan's actions (actions.py) are controllers.
"""
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from src.evaluator.scenario import (BIN_SECONDS, STEP_SECONDS, closure_steps, lane_closures,
                                    reroute_window, scene_speeds)
from src.twin.common import require_command
from src.twin.network_sources import sha256

QUEUE_PERIOD_SECONDS = 10


def rerouters(scenario, clearance_min):
    """SUMO rerouter elements for the closure: who turns off, and which lanes are closed to traffic."""
    closure = scenario["closure"]
    edges, out = " ".join(closure.get("reroute_at_edges", [])), ""
    window = reroute_window(scenario, clearance_min)
    if window:
        out += (f'<rerouter id="closure" edges="{edges}"><interval begin="{window[0]}" end="{window[1]}">'
                f'<closingReroute id="{closure["edge_id"]}"/></interval></rerouter>')
    lanes = lane_closures(scenario, clearance_min)
    if lanes:
        seen_from = " ".join(closure["scene"].get("move_over_at_edges", closure["reroute_at_edges"]))
        out += f'<rerouter id="lanes" edges="{seen_from}">' + "".join(
            f'<interval begin="{begin}" end="{end}">' + "".join(
                f'<closingLaneReroute id="{closure["edge_id"]}_{i}" disallow="all"/>' for i in indices)
            + "</interval>" for begin, end, indices in lanes) + "</rerouter>"
    return out


def prepare(scenario, files, work, clearance_min):
    """A new work folder holding a byte-identical copy of the loops file, and E's own SUMO add-ons.

    SUMO writes each loop's output next to the loops file, so the copy is what
    keeps one run's detector output apart from the next. Returns every
    additional file SUMO should load.
    """
    work = Path(work)
    work.mkdir(parents=True, exist_ok=False)
    loops = work / "detectors.add.xml"
    shutil.copyfile(files["detector_loops"], loops)
    for loop in ET.parse(loops).getroot().iter("inductionLoop"):
        (work / loop.get("file")).parent.mkdir(parents=True, exist_ok=True)
    run = scenario["run"]
    (work / "edges.add.xml").write_text(
        f'<additional><edgeData id="edges" file="edges.xml" begin="{run["warmup_seconds"]}" '
        f'end="{run["end_seconds"]}" period="{BIN_SECONDS}" excludeEmpty="true"/></additional>\n',
        encoding="utf-8")
    extras = [loops, work / "edges.add.xml"] + ([Path(files["speed_signs"])] if "speed_signs" in files else [])
    elements = rerouters(scenario, clearance_min)
    if elements:
        (work / "reroute.add.xml").write_text(f"<additional>{elements}</additional>\n", encoding="utf-8")
        extras.append(work / "reroute.add.xml")
    return extras


def command(scenario, files, work, extras):
    run = scenario["run"]
    return [require_command("sumo"), "-n", str(files["network"]), "-r", str(files["routes"]),
            "-a", ",".join(map(str, extras)),
            "--begin", "0", "--end", str(run["end_seconds"]), "--step-length", str(STEP_SECONDS),
            "--seed", str(scenario["seed"]), "--max-depart-delay", "-1", "--no-step-log", "true",
            "--duration-log.statistics", "true", "--statistic-output", str(work / "statistics.xml"),
            "--tripinfo-output", str(work / "tripinfo.xml"),
            "--tripinfo-output.write-unfinished", "true",
            "--tripinfo-output.write-undeparted", "true",
            "--device.emissions.probability", "1",
            "--queue-output", str(work / "queues.xml"),
            "--queue-output.period", str(QUEUE_PERIOD_SECONDS),
            "--log", str(work / "sumo.log")]


class Closure:
    """Sets the closed lanes' speed each second: the one thing every run does."""

    def __init__(self, scenario, clearance_min):
        self.scenario, self.clearance = scenario, clearance_min
        self.steps = closure_steps(scenario, clearance_min)
        self.edge = scenario["closure"]["edge_id"]
        self.original, self.closed, self.set, self.approach = {}, set(), {}, None

    def step(self, traci, now):
        if "scene" in self.scenario["closure"]:
            return self.step_scene(traci, now)
        due = [lanes for second, lanes in self.steps if second <= now]
        wanted = {f"{self.edge}_{i}" for i in due[-1]} if due else set()
        for lane in wanted - self.closed:
            self.original.setdefault(lane, traci.lane.getMaxSpeed(lane))
            traci.lane.setMaxSpeed(lane, 0.0)
        for lane in self.closed - wanted:
            traci.lane.setMaxSpeed(lane, self.original[lane])
        self.closed = wanted

    def step_scene(self, traci, now):
        closure = self.scenario["closure"]
        if self.approach is None:
            self.approach = [f"{edge}_{i}" for edge in closure["scene"]["approach_edges"]
                             for i in range(traci.edge.getLaneNumber(edge))]
        on_edge, approach = scene_speeds(self.scenario, self.clearance, now)
        wanted = {f"{self.edge}_{i}": on_edge / 3.6 for i in range(closure["lanes_total"])}
        wanted.update({lane: approach / 3.6 for lane in self.approach})
        for lane, speed in wanted.items():
            if self.set.get(lane) != speed:
                traci.lane.setMaxSpeed(lane, speed)
                self.set[lane] = speed


def run(scenario, files, work, clearance_min, controllers=()):
    """Simulate to the end of the run or stop at the wall-clock limit. Returns the run's health.

    `controllers` act after the closure each second. P0 on a scenario with no
    driver behaviour passes none.
    """
    import traci
    closure = Closure(scenario, clearance_min)
    work = Path(work)
    extras = prepare(scenario, files, work, clearance_min)
    before = {name: sha256(path) for name, path in files.items()}
    if sha256(extras[0]) != before["detector_loops"]:
        raise RuntimeError("The loops copy differs from the captured loops file")
    limit, started = scenario["run"]["wall_timeout_seconds"], time.monotonic()
    traci.start(command(scenario, files, work, extras), label=work.name,
                stdout=subprocess.DEVNULL)                 # SUMO's messages are kept in sumo.log
    try:
        version = traci.getVersion()[1]
        if scenario["sumo_version"] not in version:
            raise RuntimeError(f"Scenario pins SUMO {scenario['sumo_version']}; running {version}")
        if "vehicles" in scenario:
            traci.vehicletype.setLength(scenario["vehicles"]["type"], scenario["vehicles"]["length_m"])
        timed_out = False
        while traci.simulation.getTime() < scenario["run"]["end_seconds"]:
            now = traci.simulation.getTime()
            closure.step(traci, now)
            for controller in controllers:
                controller.step(traci, now)
            traci.simulationStep()
            if time.monotonic() - started > limit:
                timed_out = True
                break
        final_time = traci.simulation.getTime()
    finally:
        traci.close()
    if {name: sha256(path) for name, path in files.items()} != before:
        raise RuntimeError("A simulation input changed during the run; the run is void")
    stats = ET.parse(work / "statistics.xml").getroot()
    vehicles, teleports = stats.find("vehicles").attrib, stats.find("teleports").attrib
    edge = scenario["closure"]["edge_id"]
    return {
        "complete": not timed_out and final_time >= scenario["run"]["end_seconds"],
        "final_time_seconds": final_time,
        "wall_seconds": round(time.monotonic() - started, 1),
        "sumo_version": version,
        "closure_steps": [{"second": second, "lanes_closed": [f"{edge}_{i}" for i in lanes]}
                          for second, lanes in closure.steps],
        "drivers_rerouted_during_seconds": reroute_window(scenario, clearance_min),
        "vehicles_loaded": int(vehicles["loaded"]),
        "vehicles_inserted": int(vehicles["inserted"]),
        "vehicles_running_at_end": int(vehicles["running"]),
        "vehicles_waiting_to_enter_at_end": int(vehicles["waiting"]),
        "teleports": {name: int(teleports[name]) for name in ("total", "jam", "yield", "wrongLane")},
    }
