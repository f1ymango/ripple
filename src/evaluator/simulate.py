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
LET_IN_CHECK_SECONDS = 5
# SUMO's lane-change mode with a TraCI request obeyed while still avoiding a
# collision (bits 8-9 = 01); the default (1621) also waits for a safe gap, which
# a queue that never opens one does not give.
LET_IN_MODE = 0b10101010101
LANE_END_M = 20          # "at the end of a lane": this close to where it stops
LOOK_AHEAD_EDGES = 3     # how far along its route a lane must lead (the scene's last edges are short)
HOLD_WITHIN_M = 30       # a driver behind in the wanted lane closer than this ...
HOLD_BELOW_MS = 3.0      # ... and already this slow holds back; a faster one is left alone
# Merging in turn (the scene's merge_in_turn): drivers in a lane shut ahead keep to it along the approach
# (no lane changes of their own: lane-change mode 0) and move over at its end when it is their turn. SUMO's
# own lane-change mode is restored once they are in a lane that leads on.
KEEP_LANE_MODE = 0b0100000000      # no lane change of its own; a TraCI request still avoids collisions
DEFAULT_LANE_CHANGE_MODE = 1621
TURN_HOLD_SECONDS = 2
TURN_GIVE_UP_SECONDS = 120   # a driver kept waiting this long at the end goes at the next room, turn or not
MERGE_ZONE_M = 150           # drivers move over, in turn, while rolling along this last stretch of their lane
GAP_HEADWAY_S, GAP_SPACE_M, GAP_SECONDS = 1.0, 2.5, 4.0   # the driver behind leaves room as if behind the one moving over


def let_in_edges(closure):
    """Where a stuck driver is let in: the approach, where drivers are sent round, and the scene's let_in_edges.

    With merging in turn the approach is left to that rule (Closure.merge_in_turn).
    """
    approach = [] if closure["scene"].get("merge_in_turn") else closure["scene"]["approach_edges"]
    return list(dict.fromkeys(approach + closure.get("reroute_at_edges", [])
                              + closure["scene"].get("let_in_edges", [])))


def leads_on(traci, lane, edges):
    """Whether `lane` connects, lane by lane through open lanes, along `edges` (as far as they go)."""
    if not edges:
        return True
    for link in traci.lane.getLinks(lane):
        to = link[0]
        if to.rsplit("_", 1)[0] == edges[0] and "passenger" not in traci.lane.getDisallowed(to) \
                and (not traci.lane.getAllowed(to) or "passenger" in traci.lane.getAllowed(to)):
            if leads_on(traci, to, edges[1:]):
                return True
    return False


def rerouters(scenario, clearance_min):
    """SUMO rerouter elements for the closure: who turns off, and which lanes are closed to traffic."""
    closure = scenario["closure"]
    edges, out = " ".join(closure.get("reroute_at_edges", [])), ""
    window = reroute_window(scenario, clearance_min)
    if window and "detour" not in closure:                  # with a named detour, Closure sends drivers round itself
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
        self.window, self.sent_round = reroute_window(scenario, clearance_min), set()
        self.let_in_now = set()                             # every driver let in, for the run report
        self.merged_into = {}                               # merging in turn: lane -> drivers who moved into it
        self.lane_mode_set = {}                             # ... drivers whose lane-change mode E set: keep or turn
        self.turn_until = {}                                # ... drivers asked to move over, until when
        self.turn_target = {}                               # ... and from which lane to which
        self.last_in = {}                                   # ... (approach, lane) -> who last went through its end
        self.near_end = {}                                  # ... approach -> drivers near the end of a lane that leads on
        self.kept_usable, self.kept_looked_at = {}, {}      # keep_lane_edges: lanes that lead on, drivers looked at
        self.merges_in_turn = 0
        self.kept_on = set()                                # drivers too far into a lane onto the flyover to turn

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
        if "detour" in closure and self.window and self.window[0] <= now < self.window[1]:
            self.send_round(traci, closure)
        if closure["scene"].get("merge_in_turn"):
            self.merge_in_turn(traci, closure, now)
        wait = closure["scene"].get("let_in_after_seconds")
        if wait and now % LET_IN_CHECK_SECONDS == 0:
            self.let_in(traci, closure, wait)

    def keep_to_lanes(self, traci, closure, now, seen):
        """On the scene's keep_lane_edges, drivers in a lane shut ahead keep to it, as on the approach.

        SUMO's drivers see a lane shut 2-3 km ahead and leave it early for the one
        lane that leads on, so that lane alone queues back past Sham Tseng while
        the others run free. In TD's loops the queue holds all three lanes. Each
        driver is looked at once as it comes onto the edge, and all of them again
        whenever the lanes shut change.
        """
        edge = self.edge
        for keep in closure["scene"].get("keep_lane_edges", []):
            on = traci.edge.getLastStepVehicleIDs(keep)
            seen.update(on)
            if not on:
                continue
            route = traci.vehicle.getRoute(on[0])
            ahead = list(route[route.index(keep) + 1:]) if keep in route else []
            ahead = ahead[:ahead.index(edge) + 1] if edge in ahead else []
            lanes = traci.edge.getLaneNumber(keep)
            usable = tuple(i for i in range(lanes) if leads_on(traci, f"{keep}_{i}", ahead)) if ahead else tuple(range(lanes))
            if self.kept_usable.get(keep) != usable:
                self.kept_usable[keep], self.kept_looked_at[keep] = usable, set()
            looked_at = self.kept_looked_at[keep]
            for vehicle in on:
                if vehicle in looked_at:
                    continue
                looked_at.add(vehicle)
                if not usable or len(usable) == lanes or traci.vehicle.getLaneIndex(vehicle) in usable:
                    if self.lane_mode_set.pop(vehicle, None):
                        traci.vehicle.setLaneChangeMode(vehicle, DEFAULT_LANE_CHANGE_MODE)
                elif self.lane_mode_set.get(vehicle) != "keep":
                    traci.vehicle.setLaneChangeMode(vehicle, KEEP_LANE_MODE)
                    self.lane_mode_set[vehicle] = "keep"
            looked_at &= set(on)

    def merge_in_turn(self, traci, closure, now):
        """At the end of the approach, drivers from a lane shut ahead and the lane beside it go in turn.

        TD's loops read every lane of the queue moving at the same crawl. Left to
        SUMO, drivers in the lane that stays open queue while drivers in the lanes
        shut ahead run on past them and cut in at the end, each one let in at once,
        so the open lane's own queue stands still. Here a driver in a lane shut
        ahead keeps to it and, at its end, moves over one lane only when the last
        driver through the end of that lane was one of its own: one each, as a
        zipper. A driver behind in that lane who is already slow holds back for a
        moment if there is room ahead for the one moving over.
        """
        edge, seen = self.edge, set()
        self.keep_to_lanes(traci, closure, now, seen)
        for approach in closure["scene"]["approach_edges"]:
            lanes = traci.edge.getLaneNumber(approach)
            usable = [i for i in range(lanes) if leads_on(traci, f"{approach}_{i}", [edge])]
            on_approach = traci.edge.getLastStepVehicleIDs(approach)
            seen.update(on_approach)
            if not usable or (len(usable) == lanes and not self.lane_mode_set):
                self.near_end.pop(approach, None)
                continue
            where = {v: (traci.vehicle.getLaneIndex(v), traci.vehicle.getLanePosition(v)) for v in on_approach}
            length = traci.lane.getLength(f"{approach}_0")
            for vehicle, (start, target) in list(self.turn_target.items()):
                if vehicle in where and where[vehicle][0] == target:      # it moved over
                    del self.turn_target[vehicle]
                    self.last_in[(approach, target)] = "merged"
                    if vehicle not in self.merged_into.get(start, ()):
                        self.last_in[(approach, start)] = "own"            # one of that lane's own went through its end
                elif vehicle not in where:
                    del self.turn_target[vehicle]
            for vehicle, lane in self.near_end.get(approach, {}).items():
                if vehicle not in where and vehicle not in self.merged_into.get(lane, ()):
                    self.last_in[(approach, lane)] = "own"                 # drove on through the end of its lane
            self.near_end[approach] = {v: lane for v, (lane, pos) in where.items()
                                       if lane in usable and length - pos <= HOLD_WITHIN_M}
            front = {}
            for vehicle, (lane, position) in where.items():
                if lane in usable:
                    if self.lane_mode_set.pop(vehicle, None):
                        traci.vehicle.setLaneChangeMode(vehicle, DEFAULT_LANE_CHANGE_MODE)
                    continue
                if self.turn_until.get(vehicle, -1) <= now and self.lane_mode_set.get(vehicle) != "keep":
                    traci.vehicle.setLaneChangeMode(vehicle, KEEP_LANE_MODE)
                    self.lane_mode_set[vehicle] = "keep"
                if lane not in front or position > front[lane][1]:
                    front[lane] = (vehicle, position)
            for lane, (vehicle, position) in front.items():
                if self.turn_until.get(vehicle, -1) > now or length - position > MERGE_ZONE_M:
                    continue
                target = min(usable, key=lambda i: abs(i - lane))
                step = lane + (1 if target > lane else -1)
                own_waiting = any(other_lane == step and pos >= position - HOLD_WITHIN_M
                                  and v not in self.merged_into.get(step, ())
                                  for v, (other_lane, pos) in where.items())
                waited = traci.vehicle.getWaitingTime(vehicle)
                # turns only into a lane that leads on; into another lane shut ahead a driver moves over at once
                if (step in usable and self.last_in.get((approach, step)) == "merged" and own_waiting
                        and waited < TURN_GIVE_UP_SECONDS):
                    continue                                # the last one through moved over: the lane's own driver next
                side = 0b001 if step < lane else 0b000
                leaders = traci.vehicle.getNeighbors(vehicle, side | 0b010)
                followers = [(f, gap) for f, gap in traci.vehicle.getNeighbors(vehicle, side)
                             if -traci.vehicle.getLength(vehicle) < gap < HOLD_WITHIN_M]
                if waited >= TURN_GIVE_UP_SECONDS:          # kept too long: the slow driver behind stops for it
                    for follower, gap in followers:
                        if traci.vehicle.getSpeed(follower) < HOLD_BELOW_MS:
                            traci.vehicle.slowDown(follower, 0.0, float(TURN_HOLD_SECONDS))
                elif traci.vehicle.getSpeed(vehicle) < HOLD_BELOW_MS and (not leaders or leaders[0][1] >= 0):
                    for follower, gap in followers:         # slow, with room ahead: the driver behind leaves room
                        traci.vehicle.openGap(follower, GAP_HEADWAY_S, GAP_SPACE_M, GAP_SECONDS, 1.0, -1, vehicle)
                traci.vehicle.setLaneChangeMode(vehicle, LET_IN_MODE)
                traci.vehicle.changeLane(vehicle, step, float(TURN_HOLD_SECONDS))
                self.turn_until[vehicle] = now + TURN_HOLD_SECONDS
                self.turn_target[vehicle] = (lane, step)
                self.lane_mode_set[vehicle] = "turn"
                if vehicle not in self.merged_into.setdefault(step, set()):
                    self.merged_into[step].add(vehicle)
                    self.merges_in_turn += 1
        for vehicle in [v for v in self.lane_mode_set if v not in seen]:
            del self.lane_mode_set[vehicle]                 # left the approach (or the road) with its mode still set
            try:
                traci.vehicle.setLaneChangeMode(vehicle, DEFAULT_LANE_CHANGE_MODE)
            except traci.TraCIException:
                pass

    def let_in(self, traci, closure, wait):
        """A driver stopped `wait` seconds at the end of a lane that cannot take it on its way is let in.

        Without this SUMO lifts such a driver off the road after five minutes (a
        wrong-lane teleport) and the lane behind it stands still meanwhile. On
        the road the queue beside it lets it in: a slow driver just behind in the
        lane it needs holds back for a few seconds, and it moves over one lane as
        soon as that leaves room. It is asked again at the next check while it
        still needs to.
        """
        for edge in let_in_edges(closure):
            for vehicle in traci.edge.getLastStepVehicleIDs(edge):
                if traci.vehicle.getWaitingTime(vehicle) < wait:
                    continue
                lane = traci.vehicle.getLaneIndex(vehicle)
                if traci.lane.getLength(f"{edge}_{lane}") - traci.vehicle.getLanePosition(vehicle) > LANE_END_M:
                    continue
                route, here = traci.vehicle.getRoute(vehicle), traci.vehicle.getRouteIndex(vehicle)
                ahead = list(route[here + 1:here + 1 + LOOK_AHEAD_EDGES])
                usable = [i for i in range(traci.edge.getLaneNumber(edge)) if leads_on(traci, f"{edge}_{i}", ahead)]
                if not usable or lane in usable:
                    continue
                target = min(usable, key=lambda i: abs(i - lane))
                step = lane + (1 if target > lane else -1)
                for follower, gap in traci.vehicle.getNeighbors(vehicle, 0b001 if step < lane else 0b000):
                    if gap < HOLD_WITHIN_M and traci.vehicle.getSpeed(follower) < HOLD_BELOW_MS:
                        traci.vehicle.slowDown(follower, 0.0, float(LET_IN_CHECK_SECONDS))
                traci.vehicle.setLaneChangeMode(vehicle, LET_IN_MODE)
                traci.vehicle.changeLane(vehicle, step, float(LET_IN_CHECK_SECONDS))
                self.let_in_now.add(vehicle)

    def send_round(self, traci, closure):
        """Every lane is shut: a driver on `reroute_at_edges` heading for it takes the detour, then their own route."""
        replace, detour = closure["detour"]["replace"], closure["detour"]["with"]
        for edge in closure["reroute_at_edges"]:
            for vehicle in traci.edge.getLastStepVehicleIDs(edge):
                route, here = traci.vehicle.getRoute(vehicle), traci.vehicle.getRouteIndex(vehicle)
                if replace[0] not in route[here:]:
                    continue
                first = route.index(replace[0], here)
                if list(route[first:first + len(replace)]) != replace:
                    continue
                if (route[here] in closure["scene"].get("committed_edges", []) and first == here + 1
                        and not any(link[0].rsplit("_", 1)[0] == detour[0]
                                    for link in traci.lane.getLinks(traci.vehicle.getLaneID(vehicle)))):
                    self.kept_on.add(vehicle)               # in a lane onto the flyover, too late to change: goes on
                    continue
                try:
                    traci.vehicle.setRoute(vehicle, list(route[here:first]) + detour
                                           + list(route[first + len(replace):]))
                except traci.TraCIException:
                    continue                                # on a junction just now: tried again next second
                self.sent_round.add(vehicle)


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
        **({"drivers_sent_round_by_the_detour": len(closure.sent_round)} if "detour" in scenario["closure"] else {}),
        **({"drivers_already_committed_kept_on": len(closure.kept_on)}
           if scenario["closure"].get("scene", {}).get("committed_edges") else {}),
        **({"drivers_let_in_at_a_lane_end": len(closure.let_in_now)}
           if scenario["closure"].get("scene", {}).get("let_in_after_seconds") else {}),
        **({"drivers_merging_in_turn": closure.merges_in_turn}
           if scenario["closure"].get("scene", {}).get("merge_in_turn") else {}),
        "vehicles_loaded": int(vehicles["loaded"]),
        "vehicles_inserted": int(vehicles["inserted"]),
        "vehicles_running_at_end": int(vehicles["running"]),
        "vehicles_waiting_to_enter_at_end": int(vehicles["waiting"]),
        "teleports": {name: int(teleports[name]) for name in ("total", "jam", "yield", "wrongLane")},
    }
