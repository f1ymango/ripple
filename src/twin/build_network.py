import argparse
import sys
from pathlib import Path

from src.twin.common import load_json, require_command, resolve, run, sumo_tools


def main():
    ap = argparse.ArgumentParser(description="Download an OSM extract and convert it to SUMO.")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = load_json(resolve(args.config))
    west, south, east, north = cfg["osm_bbox"]
    osm = resolve(cfg.get("osm_output", "sim/work/osm/aberdeen.osm.xml"))
    net = resolve(cfg.get("network", "sim/aberdeen.net.xml"))
    osm.parent.mkdir(parents=True, exist_ok=True)
    net.parent.mkdir(parents=True, exist_ok=True)
    osm_get = sumo_tools() / "osmGet.py"
    # osmGet expects one comma-separated bbox and writes PREFIX_bbox.osm.xml.
    prefix = osm.name.removesuffix(".osm.xml")
    downloaded_osm = osm.parent / f"{prefix}_bbox.osm.xml"
    servers = [item.strip() for item in cfg.get("osm_servers", "hpi,pcoffee,oapi").split(",") if item.strip()]
    if not downloaded_osm.exists():
        last_error = None
        for server in servers:
            try:
                print(f"Trying OpenStreetMap download server: {server}")
                run([sys.executable, osm_get, "--bbox", f"{west},{south},{east},{north}",
                     "--prefix", prefix, "--output-dir", osm.parent, "--url", server,
                     "--retries", "0", "--verbose"])
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                print(f"That server did not complete; trying the next one. ({exc})")
        if last_error is not None:
            raise RuntimeError(f"Could not download OSM data from any server: {servers}") from last_error
    if not downloaded_osm.exists():
        raise FileNotFoundError(f"The downloader finished but expected file is missing: {downloaded_osm}")
    geometry = ["--geometry.split", "true"] if cfg.get("geometry_split") else ["--geometry.remove", "true"]
    cmd = [require_command("netconvert"), "--osm-files", downloaded_osm, "--output-file", net,
           "--junctions.join", "true", "--tls.join", "true", "--roundabouts.guess", "true",
           "--lefthand", "--keep-edges.by-vclass", "passenger", *geometry,
           "--output.street-names", "true"]
    cmd += ["--keep-edges.in-geo-boundary", f"{west},{south},{east},{north}"]
    if cfg.get("netconvert_config"):
        cmd += ["--configuration-file", resolve(cfg["netconvert_config"])]
    run(cmd)
    print(f"Draft network written: {net}\nInspect and hand-correct before calibration.")


if __name__ == "__main__":
    main()
