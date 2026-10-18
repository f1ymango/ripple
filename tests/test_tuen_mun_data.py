"""The Tuen Mun playback adapter keeps measured and missing readings distinct."""
from pathlib import Path

import pandas as pd

from src.console.tuen_mun_data import DEFAULT_OBSERVATIONS, load_playback


FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]


def test_frozen_archive_loads_real_detector_window():
    detectors, bins = load_playback()

    assert DEFAULT_OBSERVATIONS.is_file()
    assert len(detectors) == 27
    assert len(bins) == 27 * 42
    assert bins["bin_start"].nunique() == 42
    assert bins.iloc[0]["bin_start"] == "2026-04-15T17:00:00+08:00"
    assert bins.iloc[-1]["bin_start"] == "2026-04-15T20:25:00+08:00"
    assert str(bins["bin_time"].dt.tz) == "Asia/Hong_Kong"
    assert bins["bin_minutes"].unique().tolist() == [5]
    assert detectors["latitude"].between(-90, 90).all()
    assert detectors["longitude"].between(-180, 180).all()


def test_missing_count_and_speed_are_unknown_not_no_vehicles():
    _, bins = load_playback(FIXTURES / "mock_tuen_mun_observations.json")

    assert bins["state"].tolist() == ["unknown", "no_vehicles", "speed", "unknown"]
    assert pd.isna(bins.loc[0, "volume_observed"])
    assert pd.isna(bins.loc[0, "speed_kmh"])
    assert bins.loc[1, "volume_observed"] == 0
    assert bins.loc[2, "speed_kmh"] == 0
    assert pd.isna(bins.loc[2, "volume_observed"])


def test_optional_placements_add_specific_road_names_without_moving_detectors():
    placement = ROOT / "sim" / "tuen-mun" / "detectors-placement.json"
    original, _ = load_playback()
    named, _ = load_playback(placements_path=placement)

    assert named.loc[0, "road_en"].startswith("Tuen Mun Road near Yau Kom Tau")
    assert named[["latitude", "longitude"]].equals(original[["latitude", "longitude"]])
