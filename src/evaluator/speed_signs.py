"""Speed signs for an incident run: which roads move at a given speed, and where the model must make its own.

    python -m src.evaluator.speed_signs --build sim/work/p0-signs \\
        --inputs sim/work/p0-replay/twin-inputs_20260515_no-mainline-join.json \\
        --observations sim/work/p0-replay/detectors.json \\
        --ordinary-only AID01101 AID01102 AID01103 AID01104 \\
        --drop-edge 44419212 814979901#0 1198059118 1198059119 1198059120 \\
        --out sim/work/p0-replay-speeds/speeds.add.xml

`--build` is what src/twin/flow_balance_demand.py wrote for the run's hours:
one sign per chain edge, showing the ordinary mornings' quarter-hour speed of
the detector the edge leads to. This tool rewrites the speeds and keeps the
signs' places.

Three kinds of road come out:

  refreshed       each quarter-hour shows the speed the detector itself
                  measured in the quarter-hour before, on the replay morning.
                  A live twin could do this 15 minutes behind the road. Where
                  the detector measured nothing in that quarter-hour, the sign
                  shows the ordinary mornings' speed. These detectors' speeds
                  are inputs: their speed error says how well the last
                  quarter-hour predicts the next, not how well the model does.
  ordinary only   `--ordinary-only` detectors never take a speed from the
                  replay morning. Use it for the stretch an incident queues
                  on, so that the queue has to form by itself.
  no sign         `--drop-edge` edges keep the network's limit. E sets the
                  speed of the closed edge and of the crash scene itself.

A sidecar `<out>.json` lists every detector's kind and, for a refreshed one,
each quarter-hour's speed against the ordinary mornings'.
"""
import argparse
import datetime as dt
import json
import xml.etree.ElementTree as ET

from src.twin.common import load_json, resolve

MIN_SIGN_KMH = 5.0         # src/twin/flow_balance_demand.py shows no sign under 5 km/h


def own_profile(observations, minutes):
    """{detector: {"HH:MM": km/h}} from the replay morning's five-minute speeds.

    The vehicle-weighted harmonic mean per slot, as speed_profiles in
    src/loaders/twin_inputs.py; a bin with no count weighs as one vehicle.
    """
    out = {}
    for detector in observations["detectors"]:
        slots = {}
        for obs in detector["observations"]:
            if not obs.get("speed_kmh") or obs["speed_kmh"] <= 0:
                continue
            t = dt.datetime.fromisoformat(obs["time"])
            key = f"{t.hour:02d}:{t.minute - t.minute % minutes:02d}"
            weight = obs.get("count") or 1
            acc = slots.setdefault(key, [0.0, 0.0])
            acc[0] += weight
            acc[1] += weight / obs["speed_kmh"]
        out[detector["id"]] = {key: w / inv for key, (w, inv) in slots.items()}
    return out


def refreshed(ordinary, own):
    """(profile, ratios to the ordinary speed): each slot shows the speed measured in the slot before."""
    keys = sorted(ordinary)
    profile, ratios = dict(ordinary), {}
    for prev, key in zip(keys, keys[1:]):
        if prev in own:
            profile[key], ratios[key] = round(own[prev], 2), round(own[prev] / ordinary[key], 3)
    return profile, ratios


def build(signs_root, detector_by_edge, inputs, observations, ordinary_only, drop_edges, begin, end_seconds):
    """(additional element, report). `signs_root` is flow_balance_demand's speeds file, parsed."""
    minutes = inputs["speed_profile_minutes"]
    own = own_profile(observations, minutes)
    day = dt.date.fromisoformat(inputs["day"])
    profiles, report = {}, {}
    for detector in sorted(set(detector_by_edge.values())):
        ordinary = inputs["speed_profile_kmh"][detector]
        if detector in ordinary_only or detector not in own or not own[detector]:
            kind = "ordinary only" if detector in ordinary_only else "ordinary only: no speed measured on the replay morning"
            profiles[detector], ratios = dict(ordinary), {}
        else:
            kind = "refreshed"
            profiles[detector], ratios = refreshed(ordinary, own[detector])
        report[detector] = {"kind": kind, "speed_over_ordinary": ratios, "edges": 0}
    out = ET.Element("additional")
    for sign in signs_root.iter("variableSpeedSign"):
        edge = sign.get("id")[len("vss_"):]
        if edge in drop_edges:
            continue
        detector = detector_by_edge[edge]
        new = ET.SubElement(out, "variableSpeedSign", id=sign.get("id"), lanes=sign.get("lanes"))
        for key, kmh in sorted(profiles[detector].items()):
            t = (dt.datetime.combine(day, dt.time(int(key[:2]), int(key[3:])), begin.tzinfo) - begin).total_seconds()
            if t + minutes * 60 > 0 and t < end_seconds:
                ET.SubElement(new, "step", time=f"{max(t, 0):.0f}", speed=f"{max(kmh, MIN_SIGN_KMH) / 3.6:.2f}")
        report[detector]["edges"] += 1
    unsigned = sorted(d for d, row in report.items() if not row["edges"])
    return out, {"day": inputs["day"], "ordinary_days": inputs["ordinary_days"], "slot_minutes": minutes,
                 "edges_left_unsigned": sorted(drop_edges),
                 "detectors_with_no_signed_edge": unsigned, "detectors": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", required=True, help="Folder flow_balance_demand wrote: speeds.add.xml and build.json")
    parser.add_argument("--inputs", required=True, help="Data's twin inputs: the ordinary mornings' speed profile")
    parser.add_argument("--observations", required=True, help="The replay morning's five-minute observations")
    parser.add_argument("--ordinary-only", nargs="*", default=[], metavar="DETECTOR")
    parser.add_argument("--drop-edge", nargs="*", default=[], metavar="EDGE")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build_dir = resolve(args.build)
    made = load_json(build_dir / "build.json")
    signs, report = build(ET.parse(build_dir / "speeds.add.xml").getroot(), made["speed_detector_by_edge"],
                          load_json(resolve(args.inputs)), load_json(resolve(args.observations)),
                          set(args.ordinary_only), set(args.drop_edge),
                          dt.datetime.fromisoformat(made["begin"]), made["end_seconds"])
    out = resolve(args.out)
    if out.exists():
        raise ValueError(f"{out} exists; a sign file is a hashed simulation input and is never overwritten")
    out.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(signs)
    ET.ElementTree(signs).write(out, encoding="utf-8", xml_declaration=True)
    out.with_suffix(out.suffix + ".json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    kinds = [row["kind"].split(":")[0] for row in report["detectors"].values() if row["edges"]]
    print(f"{len(signs)} signs -> {out}: {kinds.count('refreshed')} detectors refreshed, "
          f"{kinds.count('ordinary only')} ordinary only")


if __name__ == "__main__":
    main()
