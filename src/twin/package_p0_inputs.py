"""Package the exact provisional P0 inputs with portable detector outputs.

This contains measured observations and generated SUMO inputs, not FCD or a
validated result. Source hashes in the manifest distinguish it from a reviewed
network release.
"""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
PREFIX = "sim/work/p0-replay"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def xml_bytes(tree):
    return ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-worktree", type=Path, required=True)
    parser.add_argument("--generated-loops", type=Path, required=True)
    parser.add_argument("--prepared-routes", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_worktree.resolve()
    files = {
        "network.net.xml": source / "sim/work/aberdeen.flow-balance-buslane.net.xml",
        "demand.rou.xml": args.prepared_routes.resolve(),
        "detectors.json": source / "sim/scenarios/detectors.json",
        "base-aberdeen.net.xml": source / "sim/work/aberdeen.net.xml",
        "aberdeen-flow-balance-buslane.con.xml": source / "sim/scenarios/aberdeen-flow-balance-buslane.con.xml",
        "aberdeen-flow-balance.edg.xml": source / "sim/scenarios/aberdeen-flow-balance.edg.xml",
        "twin-inputs_20260515_no-mainline-join.json": source / "sim/scenarios/twin-inputs_20260515_no-mainline-join.json",
    }
    payloads = {name: path.read_bytes() for name, path in files.items()}
    loops_source = args.generated_loops.resolve()
    loops = ET.parse(loops_source)
    for loop in loops.getroot().findall("inductionLoop"):
        loop.set("file", f"results/e1_{loop.get('id')}.xml")
    payloads["detectors.add.xml"] = xml_bytes(loops)
    config = {
        "network": f"{PREFIX}/network.net.xml",
        "routes": f"{PREFIX}/demand.rou.xml",
        "detector_additional": f"{PREFIX}/detectors.add.xml",
        "output_dir": f"{PREFIX}/outputs",
        "fcd_output": f"{PREFIX}/outputs/p0.fcd.xml",
        "seed": 2026, "begin": 0, "end": 11400,
        "step_length": 1, "max_depart_delay": -1, "fcd_period": 10,
        "incident": {"edge_id": "44419212", "start": 5400,
                     "duration_seconds": 4020,
                     "phases": [{"offset_seconds": 0, "lane_indices": [0]},
                                {"offset_seconds": 2460, "lane_indices": "all"}]},
    }
    payloads["p0.json"] = (json.dumps(config, indent=2) + "\n").encode()
    payloads["evaluate.json"] = b'{"observation_start_sim_seconds": 1800}\n'
    payloads["results/.keep"] = b""
    manifest = {
        "status": "PROVISIONAL ASSUMED P0 DIAGNOSTIC INPUTS; NOT INCIDENT VALIDATION",
        "incident": "IN-26-03365", "source_pr_46_commit": "647b13c",
        "assumptions": {"initial_lane": "44419212_0", "physical_onset_hkt": "08:55",
                        "all_lane_phase_hkt": "09:36", "reopen_hkt": "10:02",
                        "td_report_times_are_not_physical_transition_observations": True},
        "files": {f"{PREFIX}/{name}": {"sha256": digest(data), "bytes": len(data)}
                  for name, data in payloads.items()},
        "source_files": {str(path.relative_to(ROOT)): digest(path.read_bytes())
                         for path in [*files.values(), loops_source] if path.is_relative_to(ROOT)},
        "loop_rewrite": "Only the detector output file attributes become relative to the portable packet; lane and position stay unchanged.",
        "limitations": ["Base OSM network and detector placement are provisional.",
                        "The PR #46 flow-balance demand includes inferred route and join allocations.",
                        "No intervention, plan benefit or observed physical phase transition is claimed."],
    }
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in payloads.items():
            archive.writestr(f"{PREFIX}/{name}", data)
        archive.writestr(f"{PREFIX}/input-manifest.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(out) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive integrity check failed")
    manifest["archive_sha256"] = digest(out.read_bytes())
    manifest["archive_bytes"] = out.stat().st_size
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
