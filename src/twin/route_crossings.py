"""Deterministic E1 crossing eligibility for complete, non-repeating routes.

This predicts geometric eligibility, not delivered traffic: queues, lane changes
and travel time still require SUMO. Random/free endpoint positions are rejected.
"""
import csv
import math


def read_mapping(path):
    mapping = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            item = (row["edge_id"], float(row["position_m"]) if row.get("position_m") else None)
            did = row["detector_id"]
            if did in mapping and mapping[did] != item:
                raise ValueError(f"Inconsistent per-lane mapping for {did}")
            mapping[did] = item
    return mapping


def endpoint_position(value, length, vehicle_length, departure):
    if value == "base" and departure:
        return vehicle_length + 0.1
    if value == "max" and not departure:
        return length
    try:
        position = float(value)
    except ValueError as exc:
        raise ValueError(f"Cannot predict detector crossings for endpoint position {value!r}") from exc
    if position < 0:
        position += length
    if not math.isfinite(position) or not 0 <= position <= length:
        raise ValueError(f"Endpoint {value!r} outside edge of length {length}")
    return position


def crosses_detector(path, edge_id, position, lengths, depart="0", arrival="max", vehicle_length=5):
    if len(path) != len(set(path)):
        raise ValueError("Repeated-edge routes require crossing multiplicities, not binary incidence")
    if edge_id not in path:
        return False
    # Legacy two-column mappings have no position information. Retain their
    # former behaviour, but the fitter explicitly reports these missing positions.
    if position is None:
        return True
    if not math.isfinite(position) or not 0 <= position <= lengths[edge_id]:
        raise ValueError(f"Detector position outside edge {edge_id}")
    if path[0] == edge_id:
        start = endpoint_position(depart, lengths[edge_id], vehicle_length, True)
        if start >= position:
            return False
    if path[-1] == edge_id:
        end = endpoint_position(arrival, lengths[edge_id], vehicle_length, False)
        # nVehContrib requires complete passage, including the rear of the car.
        if end - vehicle_length <= position:
            return False
    return True
