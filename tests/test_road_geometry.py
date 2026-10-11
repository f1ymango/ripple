"""Road overlays must preserve source bends, direction and projection."""
import hashlib
import json
from pathlib import Path

import pytest

from src.console import app, road_geometry

MOCK_NETWORK = Path(__file__).parent / "fixtures" / "mock_road_geometry.net.xml"


def _load(path):
    return road_geometry.load_geometry(path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_offset_conversion_preserves_every_bend_and_separate_edges():
    geometry = _load(MOCK_NETWORK)
    roads = geometry["roads"]
    assert [r["edge_id"] for r in roads] == ["mock_bend", "mock_separate"]
    assert len(roads[0]["path"]) == 3
    for actual, expected in zip(roads[0]["path"],
                                [[114.14, 22.25], [114.145, 22.253], [114.15, 22.25]]):
        assert actual == pytest.approx(expected)
    assert roads[1]["path"][0] == pytest.approx([114.16, 22.26])
    assert all("not route advice" in r["tooltip"] for r in roads)


def test_unprojected_network_is_rejected(tmp_path):
    path = tmp_path / "mock_unprojected.net.xml"
    path.write_text(MOCK_NETWORK.read_text(encoding="utf-8").replace(
        "+proj=longlat +datum=WGS84 +no_defs", "!"), encoding="utf-8")
    with pytest.raises(ValueError, match="no geographic projection"):
        _load(path)


def test_changed_network_cannot_reuse_a_cached_identity():
    with pytest.raises(ValueError, match="Network changed"):
        road_geometry.load_geometry(MOCK_NETWORK, "0" * 64)


def test_map_keeps_basemap_and_uses_literal_pixel_widths():
    detectors = app.load_detectors()
    detectors["colour"] = [[160, 160, 160]] * len(detectors)
    for field in ("speed_label", "road_short", "evidence"):
        detectors[field] = "unavailable"
    roads = _load(MOCK_NETWORK)["roads"]
    deck = json.loads(app.build_map(detectors, roads, True).to_json())
    path_layer, detector_layer = deck["layers"]
    # An unquoted pydeck enum becomes an accessor and fills the map with blue.
    assert path_layer["widthUnits"] == "pixels"
    assert path_layer["data"] == roads
    assert detector_layer["@@type"] == "ScatterplotLayer"
    assert deck["mapProvider"] == "carto"


def test_junctions_follow_multiple_internal_lanes_and_keep_their_curves():
    geometry = _load(MOCK_NETWORK)
    junctions = geometry["junctions"]
    assert [j["lane_id"] for j in junctions] == [":b_0_0", ":b_1_0"]
    assert junctions[0]["path"][1] == pytest.approx([114.152, 22.257])
    assert junctions[1]["path"][1] == pytest.approx([114.158, 22.259])
    assert all(j["from_edge"] == "mock_bend" and j["to_edge"] == "mock_separate"
               for j in junctions)
    selected = road_geometry.select_geometry(geometry, "Full supplied network")
    assert len(selected) == 4  # two external edges plus two actual internal lanes
    # A one-road selection must not pull in an unselected destination's turn.
    geometry["roads"][1]["road_name"] = "Mock other road"
    selected = road_geometry.select_geometry(geometry, "Single road", "Mock curved road")
    assert [r["edge_id"] for r in selected] == ["mock_bend"]


def test_corridor_grouping_does_not_confuse_similarly_named_roads():
    assert road_geometry.road_group("薄扶林道 Pok Fu Lam Road") == "Alternative roads"
    assert road_geometry.road_group("舊薄扶林道 Old Pok Fu Lam Road") == "Other roads"
    assert road_geometry.road_group("黃竹坑道 Wong Chuk Hang Road") == "Main corridor"
    geometry = _load(MOCK_NETWORK)
    assert road_geometry.select_geometry(geometry, "Corridor network") == []


def test_connection_restrictions_are_respected(tmp_path):
    path = tmp_path / "mock_restricted.net.xml"
    text = MOCK_NETWORK.read_text(encoding="utf-8").replace(
        'via=":b_0_0" dir="s"', 'via=":b_0_0" allow="pedestrian" dir="s"')
    path.write_text(text, encoding="utf-8")
    assert _load(path)["junctions"] == []


def test_ordered_route_uses_only_source_edges_and_connected_turns():
    geometry = _load(MOCK_NETWORK)
    route = road_geometry.route_geometry(
        geometry, ["mock_bend", "mock_separate"], geometry["network_sha256"])
    assert [(item["kind"], item.get("edge_id") or item["lane_id"])
            for item in route] == [
                ("road", "mock_bend"), ("junction", ":b_0_0"),
                ("junction", ":b_1_0"), ("road", "mock_separate")]
    assert route[1]["path"][1] == pytest.approx([114.152, 22.257])


@pytest.mark.parametrize("edges,identity,error", [
    (["mock_bend"], "wrong", "different identities"),
    ([], "right", "no SUMO edges"),
    (["mock_walk"], "right", "unknown or inaccessible"),
    (["mock_separate", "mock_bend"], "right", "No passenger-vehicle connection"),
])
def test_route_preview_fails_closed_on_unmatched_inputs(edges, identity, error):
    geometry = _load(MOCK_NETWORK)
    network_hash = (geometry["network_sha256"] if identity == "right" else identity)
    with pytest.raises(ValueError, match=error):
        road_geometry.route_geometry(geometry, edges, network_hash)
