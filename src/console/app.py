"""Ripple operator console (component G).

Week 1: a map of the corridor, coloured by detector speed.

Detector locations come from data/detectors.csv (real, committed). Speed comes
from a snapshot the data layer writes, e.g.

    python -m src.loaders.fetch detectors --start 2026-09-21T08:00 --end 2026-09-21T09:00

which produces data/detector_5min_<window>.csv. Until one exists the map still
draws the corridor, coloured grey -- we never invent a speed (CLAUDE.md rule 4).
Run with:

    streamlit run src/console/app.py

Owner: Visuals.
"""
from __future__ import annotations

import glob
import re
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DETECTORS_CSV = ROOT / "data" / "detectors.csv"
SPEED_GLOB = str(ROOT / "data" / "detector_5min_*.csv")

# Speeds at or above this are fully green, a stop is red; a linear ramp between.
FREE_FLOW_KMH = 60.0
# At or below this a detector counts as congested in the headline panel.
CONGESTED_KMH = 30.0
GREY = [160, 160, 160]


def load_detectors() -> pd.DataFrame:
    """The corridor detectors with their real coordinates, in road order."""
    return pd.read_csv(DETECTORS_CSV)


def find_speed_files() -> list[str]:
    """Snapshots the data layer has written. The plain 5-minute file (every
    bin) comes first: docs/02-data.md says use every bin for speed, and reserve
    the coverage-filtered `_cov40` file for count calibration."""
    files = glob.glob(SPEED_GLOB)
    return sorted(files, key=lambda p: ("_cov40" in p, p))


def label_speed_file(path: str) -> str:
    """Human-readable label for the snapshot dropdown."""
    name = Path(path).name
    m = re.search(r"(\d{8})-(\d{4})_(\d{4})", name)
    if m:
        day, start, end = m.groups()
        stamp = (f"{day[6:8]}/{day[4:6]} {start[:2]}:{start[2:]}"
                 f"–{end[:2]}:{end[2:]}")
    else:
        stamp = name
    return stamp + (" · calibration-filtered" if "_cov40" in name else "")


def load_speeds(path: str) -> pd.DataFrame:
    """Speeds per detector per 5-minute bin, dropping blank speeds."""
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


def build_map(detectors: pd.DataFrame) -> pdk.Deck:
    dots = pdk.Layer(
        "ScatterplotLayer", data=detectors,
        get_position="[longitude, latitude]", get_fill_color="colour",
        get_radius=50, radius_min_pixels=5, radius_max_pixels=14,
        pickable=True, opacity=0.9, stroked=True, get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
    )
    view = pdk.ViewState(
        latitude=float(detectors["latitude"].mean()),
        longitude=float(detectors["longitude"].mean()), zoom=13.5, pitch=0,
    )
    tooltip = {
        "html": "<div style='font-size:13px'><b>{detector_id}</b>"
                " &mdash; <b>{speed_label}</b></div>"
                "<div style='font-size:12px;color:#ccc'>{road_short}</div>",
        "style": {"backgroundColor": "#111", "color": "white",
                  "padding": "6px 8px"},
    }
    # Carto's street basemap keeps roads visible at every zoom, no token needed.
    return pdk.Deck(layers=[dots], initial_view_state=view,
                    tooltip=tooltip, map_provider="carto", map_style="road")


def headline(detectors: pd.DataFrame) -> None:
    """A glanceable summary above the map."""
    known = detectors.dropna(subset=["speed_kmh"])
    c1, c2, c3 = st.columns(3)
    if known.empty:
        c1.metric("Mean speed", "—")
        c2.metric("Slowest detector", "—")
        c3.metric("Congested detectors", "—")
        return
    slowest = known.loc[known["speed_kmh"].idxmin()]
    congested = int((known["speed_kmh"] <= CONGESTED_KMH).sum())
    c1.metric("Mean corridor speed", f"{known['speed_kmh'].mean():.0f} km/h")
    c2.metric(f"Slowest · {slowest['detector_id']}",
              f"{slowest['speed_kmh']:.0f} km/h",
              help=slowest["road_en"])
    c3.metric(f"Congested (≤ {CONGESTED_KMH:.0f} km/h)",
              f"{congested} of {len(known)}")


def colour_legend() -> None:
    st.markdown(
        "**Speed** &nbsp; "
        "<span style='color:#e00'>●</span> stopped &nbsp;&rarr;&nbsp; "
        "<span style='color:#e8a000'>●</span> slow &nbsp;&rarr;&nbsp; "
        f"<span style='color:#00b400'>●</span> free-flow "
        f"(≥ {FREE_FLOW_KMH:.0f} km/h) &nbsp;&middot;&nbsp; "
        "<span style='color:#a0a0a0'>●</span> no reading",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Ripple — corridor detectors", layout="wide")
    st.title("Ripple — Aberdeen corridor")
    st.caption("Component G · operator console")

    detectors = load_detectors()
    speed_files = find_speed_files()

    if speed_files:
        chosen = st.sidebar.selectbox("Speed snapshot", speed_files,
                                      format_func=label_speed_file)
        speeds = load_speeds(chosen)
        bins = sorted(speeds["bin_start"].unique())
        bin_start = st.select_slider("5-minute bin", options=bins, value=bins[-1])
        window = speeds[speeds["bin_start"] == bin_start]
        speed_by_id = window.set_index("detector_id")["speed_kmh"].to_dict()
        detectors["speed_kmh"] = detectors["detector_id"].map(speed_by_id)
    else:
        detectors["speed_kmh"] = None
        st.info(
            "No speed snapshot found, so the corridor is grey. To colour by "
            "speed, ask the data layer for a window, e.g.\n\n"
            "`python -m src.loaders.fetch detectors "
            "--start 2026-09-21T08:00 --end 2026-09-21T09:00`"
        )

    detectors["colour"] = detectors["speed_kmh"].apply(speed_to_colour)
    detectors["speed_label"] = detectors["speed_kmh"].apply(
        lambda s: f"{s:.0f} km/h" if pd.notna(s) else "speed unknown")
    # The English name already ends in "- Eastbound"; drop it for a clean line.
    detectors["road_short"] = detectors["road_en"].str.split(" - ").str[0]

    headline(detectors)
    colour_legend()
    st.pydeck_chart(build_map(detectors))
    st.caption(f"{len(detectors)} detectors · data: DATA.GOV.HK / Transport Department")


if __name__ == "__main__":
    main()
