"""Ripple operator console (component G).

Week 1: a map of the corridor's 28 detectors, coloured by speed.

Locations come from data/detectors.csv (real, committed). Speed comes from a
detector snapshot the data layer writes, e.g.

    python -m src.loaders.fetch detectors --start 2026-09-21T08:00 --end 2026-09-21T09:00

which produces data/detector_5min_<window>.csv. Until one exists the map still
draws every detector, coloured grey -- we never invent a speed (see CLAUDE.md
rule 4). Run with:

    streamlit run src/console/app.py

Owner: Rorath (Visuals).
"""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DETECTORS_CSV = ROOT / "data" / "detectors.csv"
SPEED_GLOB = str(ROOT / "data" / "detector_5min_*.csv")

# Free-flow reference for the colour scale. Speeds at or above this are green,
# a stop is red; a plain green->red ramp in between.
FREE_FLOW_KMH = 60.0
GREY = [160, 160, 160]


def load_detectors() -> pd.DataFrame:
    """The 28 corridor detectors with their real coordinates."""
    return pd.read_csv(DETECTORS_CSV)


def find_speed_files() -> list[str]:
    """Detector snapshots the data layer has written, newest first."""
    return sorted(glob.glob(SPEED_GLOB), reverse=True)


def load_speeds(path: str) -> pd.DataFrame:
    """One speed per detector for a chosen 5-minute bin."""
    df = pd.read_csv(path)
    df = df[df["speed_kmh"] != ""]
    df["speed_kmh"] = pd.to_numeric(df["speed_kmh"], errors="coerce")
    return df.dropna(subset=["speed_kmh"])


def speed_to_colour(speed: float | None) -> list[int]:
    """Green (free-flow) through red (stopped); grey when speed is unknown."""
    if speed is None or pd.isna(speed):
        return GREY
    frac = max(0.0, min(1.0, speed / FREE_FLOW_KMH))
    return [int(255 * (1 - frac)), int(180 * frac), 40]


def build_map(df: pd.DataFrame) -> pdk.Deck:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[longitude, latitude]",
        get_fill_color="colour",
        get_radius=60,
        pickable=True,
        opacity=0.85,
    )
    view = pdk.ViewState(
        latitude=float(df["latitude"].mean()),
        longitude=float(df["longitude"].mean()),
        zoom=13,
        pitch=0,
    )
    tooltip = {
        "html": "<b>{detector_id}</b><br/>{road_en}<br/>"
                "{direction} &middot; {speed_label}",
        "style": {"backgroundColor": "#111", "color": "white"},
    }
    return pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip,
                    map_style="road")


def main() -> None:
    st.set_page_config(page_title="Ripple — corridor detectors", layout="wide")
    st.title("Ripple — Aberdeen corridor detectors")
    st.caption("Component G · operator console · Rorath")

    detectors = load_detectors()
    speed_files = find_speed_files()

    if speed_files:
        chosen = st.sidebar.selectbox("Speed snapshot", speed_files,
                                      format_func=lambda p: Path(p).name)
        speeds = load_speeds(chosen)
        bins = sorted(speeds["bin_start"].unique())
        bin_start = st.select_slider("5-minute bin", options=bins, value=bins[-1])
        window = speeds[speeds["bin_start"] == bin_start]
        speed_by_id = window.set_index("detector_id")["speed_kmh"].to_dict()
        detectors["speed_kmh"] = detectors["detector_id"].map(speed_by_id)
        st.caption(f"Coloured by speed — {Path(chosen).name}, bin {bin_start}")
    else:
        detectors["speed_kmh"] = None
        st.info(
            "No speed snapshot found, so every detector is grey. To colour by "
            "speed, ask the data layer for a window, e.g.\n\n"
            "`python -m src.loaders.fetch detectors "
            "--start 2026-09-21T08:00 --end 2026-09-21T09:00`"
        )

    detectors["colour"] = detectors["speed_kmh"].apply(speed_to_colour)
    detectors["speed_label"] = detectors["speed_kmh"].apply(
        lambda s: f"{s:.0f} km/h" if pd.notna(s) else "speed unknown")

    st.pydeck_chart(build_map(detectors))
    st.caption(f"{len(detectors)} detectors · data: DATA.GOV.HK / Transport Department")


if __name__ == "__main__":
    main()
