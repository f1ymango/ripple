"""Ripple operator console (component G).

Week 1: a map of the corridor, coloured by detector speed.

Detector locations come from data/detectors.csv (real, committed). Speed comes
from a snapshot the data layer writes, e.g.

    python -m src.loaders.fetch detectors --start 2026-09-21T08:00 --end 2026-09-21T09:00

which produces data/detector_5min_<window>_b<width>.csv, plus a filtered
_cov<n>.csv export for count calibration. Until one exists -- or when the one
chosen carries no speed at all -- the map still draws the corridor, coloured
grey: we never invent a speed (CLAUDE.md rule 4). Run with:

    streamlit run src/console/app.py

Owner: Visuals.
"""
from __future__ import annotations

import glob
import os
import re
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
# Tests point this at a fixture directory; everything else reads the real data/.
DATA_DIR = Path(os.environ.get("RIPPLE_DATA_DIR") or ROOT / "data")
DETECTORS_CSV = DATA_DIR / "detectors.csv"
SPEED_GLOB = str(DATA_DIR / "detector_5min_*.csv")

# The loader names its exports ..._b<width>[_cov<threshold>].csv. The `5min` in
# the stem is stale whenever --bin-minutes was not 5; the width and the filter
# threshold are what these two say.
BIN_IN_NAME = re.compile(r"_b(\d+)(?=(?:_cov\d+)?\.csv$)")
COV_IN_NAME = re.compile(r"_cov(\d+)(?=\.csv$)")

# Speeds at or above this are fully green, a stop is red; a linear ramp between.
FREE_FLOW_KMH = 60.0
# At or below this a detector counts as congested in the headline panel.
CONGESTED_KMH = 30.0
GREY = [160, 160, 160]


def load_detectors() -> pd.DataFrame:
    """The corridor detectors with their real coordinates, in road order."""
    return pd.read_csv(DETECTORS_CSV)


def coverage_threshold(path: str) -> int | None:
    """The coverage threshold a `_cov<n>` export was filtered at, or None for a
    full window. These exports are a deliberate subset -- only bins at or above
    the threshold -- so the dropdown has to say so (docs/02-data.md section 7)."""
    m = COV_IN_NAME.search(Path(path).name)
    return int(m.group(1)) if m else None


def find_speed_files() -> list[str]:
    """Snapshots the data layer has written. Full windows come first: docs/02-data.md
    says use every bin for speed, and reserve the coverage-filtered exports for
    count calibration."""
    files = glob.glob(SPEED_GLOB)
    return sorted(files, key=lambda p: (coverage_threshold(p) is not None, p))


def label_speed_file(path: str) -> str:
    """Human-readable label for the snapshot dropdown: the window, the bin width
    the file was named with, and whether it is a filtered calibration export."""
    name = Path(path).name
    m = re.search(r"(\d{8})-(\d{4})_(\d{4})", name)
    if m:
        day, start, end = m.groups()
        label = (f"{day[6:8]}/{day[4:6]} {start[:2]}:{start[2:]}"
                 f"–{end[:2]}:{end[2:]}")
    else:
        label = name
    width = BIN_IN_NAME.search(name)
    if width:
        label += f" · {width.group(1)} min"
    threshold = coverage_threshold(path)
    if threshold is not None:
        label += f" · filtered: coverage ≥ {threshold}%"
    return label


def load_speeds(path: str) -> pd.DataFrame:
    """Speeds per detector per bin, dropping blank speeds. Blank means no vehicle
    crossed the loop, not a speed of zero and not the speed limit -- see
    docs/02-data.md section 7. A quiet window can be blank throughout."""
    df = pd.read_csv(path)
    df = df[df["speed_kmh"] != ""]
    df["speed_kmh"] = pd.to_numeric(df["speed_kmh"], errors="coerce")
    return df.dropna(subset=["speed_kmh"])


def bin_minutes(speeds: pd.DataFrame) -> int | None:
    """The width these bins were computed at, from the CSV's own `bin_minutes`
    column -- the authority, because the filename still says `5min` whatever
    --bin-minutes the loader ran with. None if the column is missing or
    disagrees with itself, so the label can stay vague rather than wrong."""
    if "bin_minutes" not in speeds.columns:
        return None
    widths = pd.to_numeric(speeds["bin_minutes"], errors="coerce").dropna().unique()
    return int(widths[0]) if len(widths) == 1 else None


def label_bin(bin_start: str) -> str:
    """Clock time for the bin slider. The CSV carries a full ISO timestamp with
    an offset; every bin in a file is the same day, so the date and the zone are
    noise on a slider tick. Anything unparseable is shown as it came."""
    m = re.search(r"T(\d{2}):(\d{2})", str(bin_start))
    return f"{m.group(1)}:{m.group(2)}" if m else str(bin_start)


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

    detectors["speed_kmh"] = None
    if not speed_files:
        st.info(
            "No speed snapshot found, so the corridor is grey. To colour by "
            "speed, ask the data layer for a window, e.g.\n\n"
            "`python -m src.loaders.fetch detectors "
            "--start 2026-09-21T08:00 --end 2026-09-21T09:00`"
        )
    else:
        chosen = st.sidebar.selectbox("Speed snapshot", speed_files,
                                      format_func=label_speed_file)
        speeds = load_speeds(chosen)
        bins = sorted(speeds["bin_start"].unique())
        if not bins:
            # Every row blank: a real reading of a quiet window, not a fault.
            # Grey is the honest answer -- same as having no snapshot at all.
            st.info(
                f"`{Path(chosen).name}` carries no speed reading in any bin, so "
                "the corridor is grey. The data layer leaves speed blank when no "
                "vehicle crossed the loop (docs/02-data.md section 7), so a quiet "
                "window can be blank throughout. Pick another snapshot."
            )
        else:
            width = bin_minutes(speeds)
            bin_start = st.select_slider(
                f"{width}-minute bin" if width else "Time bin",
                options=bins, value=bins[-1], format_func=label_bin)
            window = speeds[speeds["bin_start"] == bin_start]
            speed_by_id = window.set_index("detector_id")["speed_kmh"].to_dict()
            detectors["speed_kmh"] = detectors["detector_id"].map(speed_by_id)

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
