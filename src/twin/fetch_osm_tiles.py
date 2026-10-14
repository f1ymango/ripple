"""Fetch and combine official OSM map tiles without modifying road objects.

The OSM map API limits nodes per request. This emits each distinct source node,
way and relation once; it does not create or edit geometry or tags.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

API = "https://api.openstreetmap.org/api/0.6/map"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--bbox", required=True, help="west,south,east,north")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--columns", type=int, default=2)
    p.add_argument("--rows", type=int, default=2)
    args = p.parse_args()
    west, south, east, north = map(float, args.bbox.split(","))
    if west >= east or south >= north or args.columns < 1 or args.rows < 1:
        raise ValueError("invalid bounding box or tile count")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    parts = {kind: args.out.with_suffix(f".{kind}.tmp")
             for kind in ("node", "way", "relation")}
    seen = {kind: set() for kind in parts}
    tiles = []
    try:
        with (parts["node"].open("wb") as nodes,
              parts["way"].open("wb") as ways,
              parts["relation"].open("wb") as relations):
            outputs = {"node": nodes, "way": ways, "relation": relations}
            for row in range(args.rows):
                for col in range(args.columns):
                    box = (west + (east-west)*col/args.columns,
                           south + (north-south)*row/args.rows,
                           west + (east-west)*(col+1)/args.columns,
                           south + (north-south)*(row+1)/args.rows)
                    bbox = ",".join(f"{value:.7f}" for value in box)
                    response = requests.get(API, params={"bbox": bbox}, timeout=90)
                    response.raise_for_status()
                    if not response.content.startswith(b"<?xml"):
                        raise ValueError(f"OSM did not return XML for {bbox}")
                    tile_path = args.out.with_name(f"{args.out.stem}-tile-{row}-{col}.osm.xml")
                    tile_path.write_bytes(response.content)
                    tiles.append({"bbox": bbox, "url": response.url,
                                  "path": str(tile_path), "sha256": digest(tile_path)})
                    for _, element in ET.iterparse(tile_path, events=("end",)):
                        kind = element.tag
                        if kind in outputs:
                            object_id = element.get("id")
                            if object_id not in seen[kind]:
                                seen[kind].add(object_id)
                                outputs[kind].write(ET.tostring(element, encoding="utf-8"))
                                outputs[kind].write(b"\n")
                            element.clear()
                    print(f"tile {row},{col}: {len(response.content)} bytes", flush=True)
        with args.out.open("wb") as merged:
            merged.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6" generator="ripple-source-tile-merge">\n')
            for kind in parts:
                with parts[kind].open("rb") as part:
                    while chunk := part.read(1024 * 1024):
                        merged.write(chunk)
            merged.write(b"</osm>\n")
        result = {"source_api": API, "bbox": args.bbox, "tiles": tiles,
                  "objects": {kind: len(ids) for kind, ids in seen.items()},
                  "merged_path": str(args.out), "merged_sha256": digest(args.out),
                  "operation": "deduplicate source objects by type and ID; no geometry or tag edits"}
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"{result['objects']} -> {args.out} ({result['merged_sha256']})")
    finally:
        for path in parts.values():
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
