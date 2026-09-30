"""The backup network's traffic model: queues that form, spill back and clear.

This is the cell transmission model (Daganzo, 1994), the textbook way to model
a road as a row of cells. Each stretch of road between two detectors (a "link")
is cut into cells no shorter than a car drives in one time step. Every step:

  * a cell SENDS the vehicles that can drive out of it, up to its capacity;
  * the next cell ACCEPTS as many as it has room for, up to its capacity;
  * the smaller of the two moves on.

When a cell ahead is full, the vehicles behind it wait. That is a queue, and it
grows backwards cell by cell, the way the detectors saw it grow from the
flyover back to Aberdeen Praya Road on 15 May. Vehicles are only created at the
corridor's entry and side roads and only removed at exits and the far end, so
every vehicle is accounted for (tests/test_fallback.py checks it).

Three simplifications, to state with the results:
  * traffic that joins or leaves between two detectors does so halfway along
    the link, because the detectors show only that it happens in between;
  * leaving traffic has its own slip road: it keeps leaving while the main
    road ahead is queued;
  * a detector's speed is the average speed in the cell just before it, over
    the vehicles that crossed it, not a spot speed at the loop.

Units: seconds, metres, vehicles, vehicles per hour, km/h.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

JAM_VEH_PER_KM_LANE = 140   # stopped traffic: about one vehicle per 7 m of lane


@dataclass
class Link:
    """A stretch of road that ends at a detector."""
    id: str
    length_m: float
    lanes: int
    free_speed_kmh: float
    capacity_veh_h: float              # all lanes together
    ends_at: str                       # the detector at its downstream end
    join_veh_h: float = 0.0            # traffic joining halfway along (a side road)
    exit_share: float = 0.0            # share of traffic leaving halfway along


@dataclass
class Closure:
    """An incident: one point of a link passes at most `capacity_veh_h` from `start_s` to `end_s`.

    `at` is how far along the link the blockage is (1.0 = just before the
    detector at its end). Traffic already past it drives on; traffic behind it queues.
    """
    link: str
    start_s: float
    end_s: float
    capacity_veh_h: float
    at: float = 1.0


@dataclass
class Result:
    """What the model saw, in bins: per detector, vehicles counted and their average speed."""
    bin_s: int
    counts: dict[str, list[float]]
    speeds: dict[str, list[float | None]]
    max_queue_m: dict[str, float]
    vehicle_hours: float               # time spent in the corridor, and waiting to enter it
    delay_vehicle_hours: float         # of which beyond driving it at free speed
    entered: float
    left: float                        # at exits and at the far end
    waiting_at_end: float              # still queued at the entry or a side road
    in_corridor_at_end: float
    longest_queue_m: float = 0.0       # the longest queue at any moment, across links


class Corridor:
    """One direction of road: links in a row, the first starting at `entry`."""

    def __init__(self, entry: str, links: list[Link], dt_s: float = 3.0,
                 end_capacity_veh_h: float | None = None):
        self.entry, self.links = entry, links
        # A cell must be at least as long as a car drives in one step, and every
        # link needs two cells so a side road can join halfway: shrink the step if not.
        shortest = min(l.length_m / (2 * l.free_speed_kmh / 3.6) for l in links)
        self.dt = min(dt_s, shortest)
        self.end_capacity = end_capacity_veh_h or links[-1].capacity_veh_h
        self.cell_link, self.cell_len, self.cell_speed = [], [], []    # link index, m, m/s
        self.link_first_cell = []
        for k, l in enumerate(links):
            n = max(2, math.floor(l.length_m / (l.free_speed_kmh / 3.6 * self.dt)))
            self.link_first_cell.append(len(self.cell_link))
            self.cell_link += [k] * n
            self.cell_len += [l.length_m / n] * n
            self.cell_speed += [l.free_speed_kmh / 3.6] * n

    def run(self, demand: Callable[[float], float], end_s: float, bin_s: int = 300,
            closures: list[Closure] | None = None) -> Result:
        """Drive `demand(t)` (vehicles per hour at the entry) through the corridor until `end_s`.

        Every vehicle knows where it is going: out at one of the exits, or on to
        the far end, drawn from the exit shares downstream of where it joined.
        A vehicle bound for the far end never leaves early, and one bound for an
        exit leaves by it even when the road beyond the exit is full.
        """
        closures = closures or []
        dt, links, K = self.dt, self.links, len(self.cell_link)
        # Where things happen between cells: a side road or exit halfway along each
        # link, a detector at the start of each link after the first.
        middle = {self.link_first_cell[k] + self._cells_in(k) // 2: k for k in range(len(links))}
        exits = sorted(b for b, k in middle.items() if links[k].exit_share > 0)
        D = len(exits) + 1                         # destinations: each exit in turn, then the far end
        detector_at = {self.link_first_cell[k + 1]: links[k].ends_at for k in range(len(links) - 1)}
        jam = [JAM_VEH_PER_KM_LANE / 1000 * links[self.cell_link[i]].lanes * self.cell_len[i]
               for i in range(K)]
        base = [links[self.cell_link[i]].capacity_veh_h / 3600 * dt for i in range(K)]
        wave = [min(1.0, self._wave_speed(self.cell_link[i]) * dt / self.cell_len[i]) for i in range(K)]
        blocked = [(self._cell_at(c.link, c.at), c) for c in closures]
        entry_split = self._split(0, exits, middle)
        side_split = {b: self._split(b, exits, middle) for b, k in middle.items() if links[k].join_veh_h > 0}
        n = [[0.0] * D for _ in range(K)]          # vehicles in each cell, by destination
        side_queue = {b: 0.0 for b in side_split}
        entry_queue = entered = left = vehicle_s = free_s = 0.0
        bins = math.ceil(end_s / bin_s)
        names = [self.entry] + [l.ends_at for l in links]
        counts = {d: [0.0] * bins for d in names}
        speed_sum = {d: [0.0] * bins for d in names}
        max_queue = {l.id: 0.0 for l in links}
        longest = 0.0

        for s in range(math.ceil(end_s / dt)):
            t = s * dt
            b_now = min(int(t // bin_s), bins - 1)
            cap = list(base)
            for i, c in blocked:
                if c.start_s <= t < c.end_s:
                    cap[i] = min(cap[i], c.capacity_veh_h / 3600 * dt)
            total = [sum(cell) for cell in n]
            # How many vehicles each cell can send on, and how many it can take in.
            send = [min(total[i] * self.cell_speed[i] * dt / self.cell_len[i], cap[i]) for i in range(K)]
            take = [min(cap[i], wave[i] * max(jam[i] - total[i], 0.0)) for i in range(K)]
            change = [[0.0] * D for _ in range(K)]
            out_of = [0.0] * K

            # The entry: vehicles arrive, and wait at the entry if the first cell is full.
            arriving = demand(t) / 3600 * dt
            entry_queue += arriving
            entered += arriving
            moved = min(entry_queue, take[0])
            entry_queue -= moved
            for d in range(D):
                change[0][d] += moved * entry_split[d]

            for b in range(1, K):                      # between cell b-1 and cell b
                up = b - 1
                if b in side_split:
                    arriving = links[middle[b]].join_veh_h / 3600 * dt
                    side_queue[b] += arriving
                    entered += arriving
                going = [send[up] * x / total[up] if total[up] > 1e-12 else 0.0 for x in n[up]]
                leaving = 0.0
                if b in exits:                         # its own slip road: never held up
                    j = exits.index(b)
                    leaving, going[j] = going[j], 0.0
                    change[up][j] -= leaving
                    left += leaving
                main, side = sum(going), side_queue.get(b, 0.0)
                if main + side > take[b]:              # not enough room: share it by demand
                    main, side = take[b] * main / (main + side), take[b] * side / (main + side)
                scale = main / sum(going) if sum(going) > 1e-12 else 0.0
                for d in range(D):
                    change[up][d] -= going[d] * scale
                    change[b][d] += going[d] * scale
                if b in side_split:
                    side_queue[b] -= side
                    for d in range(D):
                        change[b][d] += side * side_split[b][d]
                out_of[up] = leaving + main
                if b in detector_at:
                    self._count(counts, speed_sum, detector_at[b], b_now, main,
                                self._speed(total[up], out_of[up], up))

            out = min(send[K - 1], self.end_capacity / 3600 * dt)     # the far end
            for d in range(D):
                change[K - 1][d] -= out * n[K - 1][d] / total[K - 1] if total[K - 1] > 1e-12 else 0.0
            out_of[K - 1] = out
            left += out
            self._count(counts, speed_sum, links[-1].ends_at, b_now, out,
                        self._speed(total[K - 1], out, K - 1))
            # The entry detector reads the first cell, now that its outflow is known.
            self._count(counts, speed_sum, self.entry, b_now, moved, self._speed(total[0], out_of[0], 0))

            waiting = entry_queue + sum(side_queue.values())
            vehicle_s += (sum(total) + waiting) * dt
            free_s += sum(out_of[i] * self.cell_len[i] / self.cell_speed[i] for i in range(K))
            for i in range(K):
                for d in range(D):
                    n[i][d] = max(n[i][d] + change[i][d], 0.0)
            longest = max(longest, self._queues([sum(cell) for cell in n], max_queue))

        speeds = {d: [speed_sum[d][b] / counts[d][b] * 3.6 if counts[d][b] > 1e-9 else None
                      for b in range(bins)] for d in names}
        waiting = entry_queue + sum(side_queue.values())
        return Result(bin_s, counts, speeds, max_queue, vehicle_s / 3600,
                      (vehicle_s - free_s) / 3600, entered, left, waiting, sum(sum(c) for c in n), longest)

    def _split(self, joined_at: int, exits: list[int], middle: dict[int, int]) -> list[float]:
        """Where vehicles joining at boundary `joined_at` are going: each exit after it, then the far end."""
        split, staying = [0.0] * (len(exits) + 1), 1.0
        for j, b in enumerate(exits):
            if b > joined_at:
                share = self.links[middle[b]].exit_share
                split[j] = staying * share
                staying *= 1 - share
        split[-1] = staying
        return split

    # ------------------------------------------------------------------ helpers

    def _cell_at(self, link_id: str, at: float) -> int:
        """The cell `at` (0 to 1) of the way along the link called `link_id`."""
        k = next(i for i, l in enumerate(self.links) if l.id == link_id)
        n = self._cells_in(k)
        return self.link_first_cell[k] + min(n - 1, int(at * n))

    def _cells_in(self, k: int) -> int:
        """How many cells link k has."""
        end = self.link_first_cell[k + 1] if k + 1 < len(self.links) else len(self.cell_link)
        return end - self.link_first_cell[k]

    def _wave_speed(self, k: int) -> float:
        """How fast a queue grows backwards on link k (m/s), from its triangle of speed and capacity."""
        l = self.links[k]
        critical = l.capacity_veh_h / (l.free_speed_kmh)                  # veh/km at capacity
        return l.capacity_veh_h / (JAM_VEH_PER_KM_LANE * l.lanes - critical) / 3.6

    def _speed(self, vehicles: float, out: float, i: int) -> float:
        """Average speed in cell i (m/s): what left it, over what was in it."""
        if vehicles <= 1e-9:
            return self.cell_speed[i]
        return min(self.cell_speed[i], out * self.cell_len[i] / (vehicles * self.dt))

    @staticmethod
    def _count(counts, speed_sum, detector, b, vehicles, speed_ms) -> None:
        counts[detector][b] += vehicles
        speed_sum[detector][b] += vehicles * speed_ms

    def _queues(self, n: list[float], max_queue: dict[str, float]) -> float:
        """Per link, the longest run of cells denser than at capacity: the queue.

        Returns the longest run right now across link boundaries, where a
        queue behind an incident usually runs.
        """
        across = longest = 0.0
        for k, l in enumerate(self.links):
            critical = l.capacity_veh_h / l.free_speed_kmh / 1000             # veh/m, all lanes
            first = self.link_first_cell[k]
            run = best = 0.0
            for i in range(first, first + self._cells_in(k)):
                if n[i] / self.cell_len[i] > critical * 1.05:
                    run += self.cell_len[i]
                    across += self.cell_len[i]
                    best, longest = max(best, run), max(longest, across)
                else:
                    run = across = 0.0
            max_queue[l.id] = max(max_queue[l.id], best)
        return longest
