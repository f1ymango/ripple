"""What drivers do by themselves when they meet the queue. Not a plan action: it is in every run, P0 included.

One rule, from the scenario's `drivers_leave` block: a driver in a nearside
lane who reaches an exit while the traffic ahead is queued takes that exit
with a fixed probability, and leaves the modelled corridor. The same
probability applies, once for each minute of waiting, to a driver the queue
keeps from entering the network at all. Where they go next is outside the
model, so each one is charged `extra_minutes_outside` in the delay total
(metrics.py). A driver who is following a plan's route advice does not leave.
"""
import json
from pathlib import Path

from src.evaluator.scenario import draw

LEFT_FILE = "left-corridor.json"


class DriversLeave:
    def __init__(self, scenario, advice=None):
        self.rule, self.seed, self.advice = scenario["drivers_leave"], scenario["seed"], advice
        self.queue_ms = self.rule["queue_kmh"] / 3.6
        self.asked, self.waiting_since, self.minutes_asked, self.left = set(), {}, {}, []

    def heading_into_queue(self, vehicle, route, now):
        return (self.rule["route_crosses"] in route
                and not (self.advice and self.advice.follows(vehicle, route, now)))

    def queue_ahead(self, traci, edges):
        speeds = [traci.edge.getLastStepMeanSpeed(edge) for edge in edges
                  if traci.edge.getLastStepVehicleNumber(edge)]
        return bool(speeds) and min(speeds) < self.queue_ms

    def step(self, traci, now):
        for place in self.rule["exits"]:
            self.at_exit(traci, now, place)
        if "entry" in self.rule:
            self.at_entry(traci, now)

    def at_exit(self, traci, now, place):
        exit_edge, last = place["exit_edge"], place["decide_on"][-1]
        deciding = [vehicle for edge in place["decide_on"] for vehicle in traci.edge.getLastStepVehicleIDs(edge)
                    if (vehicle, exit_edge) not in self.asked]
        if not deciding or not self.queue_ahead(traci, place["look_ahead"]):
            return
        for vehicle in deciding:
            if traci.vehicle.getLaneIndex(vehicle) >= place["nearside_lanes"]:
                continue                                    # cannot reach the exit from here; may still move over
            self.asked.add((vehicle, exit_edge))
            route = traci.vehicle.getRoute(vehicle)
            if (last not in route or not self.heading_into_queue(vehicle, route, now)
                    or draw(self.seed, vehicle, exit_edge) >= self.rule["share"]):
                continue
            here = traci.vehicle.getRouteIndex(vehicle)
            try:
                traci.vehicle.setRoute(vehicle, list(route[here:route.index(last) + 1]) + [exit_edge])
            except traci.TraCIException:
                continue                                    # already past the turn
            self.left.append({"id": vehicle, "how": "exit", "edge": exit_edge, "second": now})

    def at_entry(self, traci, now):
        entry = self.rule["entry"]
        for vehicle in traci.simulation.getPendingVehicles():
            since = self.waiting_since.setdefault(vehicle, now)
            minute = int((now - since) // entry["after_waiting_seconds"])
            if minute < 1 or self.minutes_asked.get(vehicle, 0) >= minute:
                continue
            self.minutes_asked[vehicle] = minute
            route = traci.vehicle.getRoute(vehicle)
            if (route[0] == entry["edge"] and self.heading_into_queue(vehicle, route, now)
                    and draw(self.seed, vehicle, "entry", minute) < self.rule["share"]):
                traci.vehicle.remove(vehicle)
                self.left.append({"id": vehicle, "how": "entry", "edge": entry["edge"], "second": now,
                                  "waited_seconds": now - since})

    def save(self, work):
        (Path(work) / LEFT_FILE).write_text(json.dumps(self.left, indent=1) + "\n", encoding="utf-8")

    def report(self):
        by_edge = {}
        for row in self.left:
            by_edge[row["edge"]] = by_edge.get(row["edge"], 0) + 1
        return {"rule": "drivers who see the queue at an exit, or are kept out of the network by it, leave the corridor",
                "share": self.rule["share"], "vehicles_left": len(self.left),
                "vehicles_left_by_edge": dict(sorted(by_edge.items()))}
