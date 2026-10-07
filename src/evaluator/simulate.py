"""Run SUMO once with the scenario's lane closure. No plan logic lives here.

The closure is injected the way Simulation's src/twin/run_scenario.py does it:
the closed lanes' speed limit is set to zero for the closure and restored at
reopening, so vehicles queue rather than lose their route.
"""
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from src.evaluator.scenario import BIN_SECONDS, STEP_SECONDS, closure_steps
from src.twin.common import require_command
from src.twin.network_sources import sha256

QUEUE_PERIOD_SECONDS = 10


def prepare(scenario, files, work):
    """A new work folder holding a byte-identical copy of the loops file.

    SUMO writes each loop's output next to the loops file, so the copy is what
    keeps one run's detector output apart from the next.
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
    return loops


def command(scenario, files, work, loops):
    run = scenario["run"]
    return [require_command("sumo"), "-n", str(files["network"]), "-r", str(files["routes"]),
            "-a", f"{loops},{work / 'edges.add.xml'}",
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


def run(scenario, files, work, clearance_min, on_step=None):
    """Simulate to the end of the run or stop at the wall-clock limit. Returns the run's health.

    `on_step(traci, now)` is where a plan's actions will be applied. P0 passes none.
    """
    import traci
    steps = closure_steps(scenario, clearance_min)
    edge = scenario["closure"]["edge_id"]
    loops = prepare(scenario, files, work)
    work = Path(work)
    before = {name: sha256(path) for name, path in files.items()}
    if sha256(loops) != before["detector_loops"]:
        raise RuntimeError("The loops copy differs from the captured loops file")
    limit, started = scenario["run"]["wall_timeout_seconds"], time.monotonic()
    traci.start(command(scenario, files, work, loops), label=work.name,
                stdout=subprocess.DEVNULL)                 # SUMO's messages are kept in sumo.log
    try:
        version = traci.getVersion()[1]
        if scenario["sumo_version"] not in version:
            raise RuntimeError(f"Scenario pins SUMO {scenario['sumo_version']}; running {version}")
        original, closed, timed_out = {}, set(), False
        while traci.simulation.getTime() < scenario["run"]["end_seconds"]:
            now = traci.simulation.getTime()
            due = [lanes for second, lanes in steps if second <= now]
            wanted = {f"{edge}_{i}" for i in due[-1]} if due else set()
            for lane in wanted - closed:
                original.setdefault(lane, traci.lane.getMaxSpeed(lane))
                traci.lane.setMaxSpeed(lane, 0.0)
            for lane in closed - wanted:
                traci.lane.setMaxSpeed(lane, original[lane])
            closed = wanted
            if on_step:
                on_step(traci, now)
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
    return {
        "complete": not timed_out and final_time >= scenario["run"]["end_seconds"],
        "final_time_seconds": final_time,
        "wall_seconds": round(time.monotonic() - started, 1),
        "sumo_version": version,
        "closure_steps": [{"second": second, "lanes_closed": [f"{edge}_{i}" for i in lanes]}
                          for second, lanes in steps],
        "vehicles_loaded": int(vehicles["loaded"]),
        "vehicles_inserted": int(vehicles["inserted"]),
        "vehicles_running_at_end": int(vehicles["running"]),
        "vehicles_waiting_to_enter_at_end": int(vehicles["waiting"]),
        "teleports": {name: int(teleports[name]) for name in ("total", "jam", "yield", "wrongLane")},
    }
