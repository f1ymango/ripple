"""Prepare flow-balance routes for a no-speed-sign SUMO diagnostic.

The Data builder keeps its signed-speed vehicle-type settings when called with
``--no-speeds``. Remove only those three settings so SUMO supplies its defaults.
The flow definitions, route edges and departure attributes stay untouched.
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


DRIVER_ATTRIBUTES = ("speedFactor", "speedDev", "sigma")


def prepare(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Choose a new output path; the builder's routes are evidence")
    if destination.exists():
        raise FileExistsError(destination)
    tree = ET.parse(source)
    root = tree.getroot()
    if root.tag != "routes":
        raise ValueError("Expected a SUMO <routes> document")
    vehicle_types = root.findall("vType")
    if len(vehicle_types) != 1 or vehicle_types[0].get("id") != "DEFAULT_VEHTYPE":
        raise ValueError("Expected exactly one flow-balance DEFAULT_VEHTYPE")
    vehicle_type = vehicle_types[0]
    if not all(attribute in vehicle_type.attrib for attribute in DRIVER_ATTRIBUTES):
        raise ValueError("Expected the builder's explicit driver attributes")
    for attribute in DRIVER_ATTRIBUTES:
        del vehicle_type.attrib[attribute]
    destination.parent.mkdir(parents=True, exist_ok=True)
    tree.write(destination, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.routes, args.out)


if __name__ == "__main__":
    main()
