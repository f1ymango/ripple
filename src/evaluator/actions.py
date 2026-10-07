"""A validated plan's actions, applied in the twin. Compliance is applied here and nowhere else.

What E models, from the plan context's `active_from` until its `active_until`
or until the first lane reopens, whichever comes first:

  diversions   a driver of the od group follows the advice with probability
               share x compliance. From then on that driver takes the advised
               route in place of the closed road, wherever they are when the
               advice starts or when they set off, and does not leave the
               corridor at an exit (behaviour.py). When the advice stops, a
               driver who has not yet reached the detour goes back to the
               reopened road.
  signals      the junction's green phases for the advised route run
               `green_extend_s` longer; the other phases keep their length, so
               the cycle grows by as much.
  vms          no effect of their own: a sign is one of the ways the advice
               reaches drivers, and compliance already covers how many follow.
  pt_nudge     not modelled. E refuses a plan that uses it.

The scenario's `plan_actions` block says where each od group, route and
junction is in this network. E refuses a plan that names one it cannot place,
rather than run the do-nothing case under the plan's name.
"""
from datetime import datetime

from src.evaluator.scenario import draw, reopen_second


def has_actions(plan):
    return bool(plan["diversions"] or plan["signals"] or plan["vms"] or plan["pt_nudge"]["mode"])


def seconds_into_run(scenario, moment):
    return (datetime.fromisoformat(moment) - datetime.fromisoformat(scenario["run"]["begin"])).total_seconds()


class PlanActions:
    def __init__(self, plan, context, scenario, compliance, clearance_min):
        if plan["pt_nudge"]["mode"]:
            raise NotImplementedError("E does not model a shift to public transport, so it cannot run this plan")
        places = scenario.get("plan_actions")
        if places is None:
            raise NotImplementedError(
                "E can only run P0 on this scenario: it has no plan_actions block saying where a plan's "
                "routes and junctions are in the network")
        try:
            self.advice = [{**places["od_groups"][d["od_group"]], **places["routes"][d["via"]],
                            "od_group": d["od_group"], "probability": d["share"] * compliance}
                           for d in plan["diversions"]]
            self.signals = [{**places["signals"][s["junction_id"]], "junction_id": s["junction_id"],
                             "extend": s["green_extend_s"]} for s in plan["signals"]]
        except KeyError as missing:
            raise NotImplementedError(f"The scenario's plan_actions block does not place {missing}") from None
        self.seed = scenario["seed"]
        self.start = seconds_into_run(scenario, context["active_from"])
        self.end = min(seconds_into_run(scenario, context["active_until"]), reopen_second(scenario, clearance_min))
        self.signs = len(plan["vms"])
        self.started, self.retry, self.rerouted, self.base_program = False, set(), set(), {}
        self.group_of = {}                                  # a rerouted driver's route no longer names the closed road
        self.returned = 0

    def group(self, route):
        return next((a for a in self.advice if a["via_edge"] in route and route[-1] == a["to_edge"]), None)

    def follows(self, vehicle, route, now):
        """Does this driver follow the plan's route advice at `now`? Fixed per driver by the run's seed."""
        if not self.start <= now < self.end:
            return False
        advice = self.group(route) or self.group_of.get(vehicle)
        return bool(advice) and draw(self.seed, vehicle, "advice") < advice["probability"]

    def step(self, traci, now):
        active = self.start <= now < self.end
        if self.advice and active:
            if not self.started:
                candidates = set(traci.vehicle.getIDList())         # everyone on the road hears it at once
            else:
                candidates = set(traci.simulation.getDepartedIDList())
                if self.retry:
                    candidates |= self.retry & set(traci.vehicle.getIDList())
            self.retry = set()
            for vehicle in sorted(candidates):
                self.advise(traci, vehicle, now)
        if active != self.started:
            self.started = active
            for signal in self.signals:
                self.extend_green(traci, signal) if active else traci.trafficlight.setProgram(
                    signal["tls_id"], self.base_program[signal["tls_id"]])
            if not active:
                for vehicle in sorted(self.rerouted & set(traci.vehicle.getIDList())):
                    self.withdraw(traci, vehicle)

    def advise(self, traci, vehicle, now):
        route = traci.vehicle.getRoute(vehicle)
        advice = self.group(route)
        if not advice or draw(self.seed, vehicle, "advice") >= advice["probability"]:
            return
        here, first = traci.vehicle.getRouteIndex(vehicle), route.index(advice["via_edge"])
        after = first + len(advice["replace"])
        if here >= first or list(route[first:after]) != advice["replace"]:
            return                                          # already on the closed road, or not on the road the advice replaces
        try:
            traci.vehicle.setRoute(vehicle, list(route[max(here, 0):first]) + advice["with"] + list(route[after:]))
        except traci.TraCIException:
            self.retry.add(vehicle)                         # on a junction just now: try again next second
            return
        self.group_of[vehicle] = advice
        self.rerouted.add(vehicle)

    def withdraw(self, traci, vehicle):
        """The advice has stopped: a driver still short of the detour takes the reopened road again."""
        advice = self.group_of[vehicle]
        route, here = traci.vehicle.getRoute(vehicle), traci.vehicle.getRouteIndex(vehicle)
        first = route.index(advice["with"][0])
        if here >= first:
            return                                          # already on the detour
        try:
            traci.vehicle.setRoute(vehicle, list(route[max(here, 0):first]) + advice["replace"]
                                   + list(route[first + len(advice["with"]):]))
        except traci.TraCIException:
            return                                          # on a junction just now: keeps the detour
        self.returned += 1

    def extend_green(self, traci, signal):
        tls = signal["tls_id"]
        current = traci.trafficlight.getProgram(tls)
        logic = next(l for l in traci.trafficlight.getAllProgramLogics(tls) if l.programID == current)
        phases = [traci.trafficlight.Phase(phase.duration + (signal["extend"] if i in signal["green_phases"] else 0),
                                           phase.state) for i, phase in enumerate(logic.phases)]
        self.base_program[tls] = current
        traci.trafficlight.setProgramLogic(tls, traci.trafficlight.Logic("plan", logic.type, 0, phases))
        traci.trafficlight.setProgram(tls, "plan")

    def report(self):
        return {
            "active_seconds": [self.start, self.end],
            "diversions": [{"od_group": a["od_group"], "probability_a_driver_follows": round(a["probability"], 4)}
                           for a in self.advice],
            "vehicles_that_took_the_advised_route": len(self.rerouted),
            "of_them_back_on_the_reopened_road": self.returned,
            "signals": [{"junction_id": s["junction_id"], "green_extended_seconds": s["extend"],
                         "phases": s["green_phases"]} for s in self.signals],
            "vms": f"{self.signs} sign(s) named; no effect of their own in the twin",
        }
