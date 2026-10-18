"""Tuen Mun map paths must come from its frozen georeferenced network."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from src.console import app, road_geometry, tuen_mun_geometry


ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / "sim" / "tuen-mun" / "network.net.xml"
OBSERVATIONS = ROOT / "sim" / "tuen-mun" / "observations_20260415.json"


def test_road_names_exclude_lookalikes_and_aberdeen_roads():
    group = tuen_mun_geometry.road_group
    assert group("屯門公路 Tuen Mun Road") == tuen_mun_geometry.MAIN
    assert group("青山公路－深井段 Castle Peak Road – Sham Tseng") == tuen_mun_geometry.ALTERNATIVE
    assert group("Old Tuen Mun Road") is None
    assert group("Castle Peak Roadside") is None
    assert group("黃竹坑道 Wong Chuk Hang Road") is None


def test_overlay_preserves_real_network_paths_and_only_connected_junctions():
    sha256 = hashlib.sha256(NETWORK.read_bytes()).hexdigest()
    geometry = road_geometry.load_geometry(NETWORK, sha256)
    overlay = tuen_mun_geometry.select_overlay(geometry)
    source_roads = {road["edge_id"]: road for road in geometry["roads"]}
    roads = [record for record in overlay if record["kind"] == "road"]
    junctions = [record for record in overlay if record["kind"] == "junction"]
    selected_ids = {road["edge_id"] for road in roads}

    assert {road["group"] for road in roads} == {
        tuen_mun_geometry.MAIN, tuen_mun_geometry.ALTERNATIVE}
    assert all(road["path"] == source_roads[road["edge_id"]]["path"] for road in roads)
    assert all(j["from_edge"] in selected_ids and j["to_edge"] in selected_ids
               for j in junctions)
    assert all(record["colour"] == tuen_mun_geometry.COLOURS[record["group"]]
               for record in overlay)
    assert all("not route advice" in record["tooltip"] for record in overlay)


def test_overlay_loads_as_map_paths_and_dataframe():
    overlay = tuen_mun_geometry.load_overlay()
    frame = tuen_mun_geometry.overlay_frame()
    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == len(overlay)
    assert {"path", "colour", "width", "group", "kind"} <= set(frame.columns)

    observations = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))
    detectors = pd.DataFrame({
        "detector_id": [d["id"] for d in observations["detectors"]],
        "latitude": [d["lat"] for d in observations["detectors"]],
        "longitude": [d["lon"] for d in observations["detectors"]],
        "colour": [[160, 160, 160] for _ in observations["detectors"]],
        "speed_label": ["no reading" for _ in observations["detectors"]],
        "road_short": ["Tuen Mun Road" for _ in observations["detectors"]],
        "evidence": ["" for _ in observations["detectors"]],
    })
    deck = json.loads(app.build_map(detectors, overlay).to_json())
    assert deck["layers"][0]["@@type"] == "PathLayer"
    assert deck["layers"][0]["data"] == overlay
    assert deck["layers"][1]["@@type"] == "ScatterplotLayer"
