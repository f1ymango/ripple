"""When a P0 run is good enough to compare plans against: the one rule E, F and the console share.

docs/03-architecture.md section 4 sets the targets. A result's `validation`
block comes in two versions, and each is judged by its own rule:

  - **Counts and speed** (version 1, until 13 October 2026): GEH < 5 in at
    least 85% of count bins and speed MAPE at most 15%.
  - **Counts, free-flow speed and congestion state** (version 2, agreed by the
    team on 13 October 2026): GEH < 5 in at least 85% of count bins; speed MAPE
    at most 15% over bins measured at 30 km/h or more; the model and the
    detector agreeing on whether a speed bin is congested (under 30 km/h) in
    at least 85% of speed bins; and no wrong-lane teleport except of a driver
    stuck from the moment a lane shut. The whole-run speed MAPE stays in the
    block as information. A block is version 2 when it has
    `speed_mape_free_flow_pct`.

Why version 2: the corridor's detectors miss many vehicles in traffic under
30 km/h (results/data/count-bias_AID01106_AID01107.md), so those counts are
left out of the detector data, and a MAPE over crawling bins can only be met by
putting the measured speed into the model, which would also cap its flow
(docs/evaluator-replay-v3-2026-10-13.md). Version 2 still asks the model to be
right about where and when traffic is congested.

Meeting the targets is not enough to rank plans with version 2:
src/evaluator/ranking.py states an order only where it holds in every cell of
a grid of seeds and assumptions.
"""
import math

COUNT_TARGET = 85.0      # % of count bins with GEH < 5
SPEED_TARGET = 15.0      # speed MAPE, %
STATE_TARGET = 85.0      # % of speed bins where model and detector agree on congested or not
CONGESTED_KMH = 30.0     # a bin measured under this speed is congested

DESCRIPTION = ("GEH < 5 in at least 85% of count bins; speed MAPE at most 15% over bins measured at 30 km/h or "
               "more; model and detector agree on congested (under 30 km/h) or not in at least 85% of speed bins; "
               "no wrong-lane teleport except of a driver stuck from the moment a lane shut "
               "(03-architecture.md section 4, version 2 of 13 October 2026)")


def _number(validation, key, highest=math.inf):
    value = validation[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"validation {key} is not a number")
    if not math.isfinite(value) or not 0 <= value <= highest:
        raise ValueError(f"validation {key} is out of range")
    return value


def check(validation):
    """(met, reason): whether a P0 `validation` block meets its version's targets, and if not, why not."""
    if not isinstance(validation, dict) or not validation:
        return False, "Baseline validation is missing."
    try:
        geh = _number(validation, "geh_under_5_pct", 100)
        speed = _number(validation, "speed_mape_pct")
        if "speed_mape_free_flow_pct" not in validation:                   # version 1
            if geh < COUNT_TARGET or speed > SPEED_TARGET:
                return False, "Baseline is below the GEH or speed validation target."
            return True, ""
        free_flow = _number(validation, "speed_mape_free_flow_pct")
        state = _number(validation, "congestion_state_agreement_pct", 100)
        teleports = _number(validation, "wrong_lane_teleports_not_at_lane_shut")
    except (KeyError, ValueError):
        return False, "Baseline validation is incomplete."
    if geh < COUNT_TARGET:
        return False, "Baseline is below the GEH validation target."
    if free_flow > SPEED_TARGET:
        return False, "Baseline is above the free-flow speed error target."
    if state < STATE_TARGET:
        return False, "Baseline is below the congestion-state agreement target."
    if teleports:
        return False, "Baseline had a wrong-lane teleport other than at the moment a lane shut."
    return True, ""


def met(validation):
    return check(validation)[0]


def is_version_2(validation):
    return isinstance(validation, dict) and "speed_mape_free_flow_pct" in validation
