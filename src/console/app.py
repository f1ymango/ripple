"""Ripple operator console (component G).

Week 1: a map of the corridor, coloured by detector speed.
Week 2: playback of one archived window, bin by bin, so an incident can be
watched the way the detectors recorded it.

Detector locations come from data/detectors.csv (real, committed). Speed comes
from a snapshot the data layer writes -- for the demo incident IN-26-03365
(Fri 15 May, data/demo_shortlist.md) that is

    python -m src.loaders.fetch detectors --start 2026-05-15T07:55 --end 2026-05-15T10:35

which produces data/detector_5min_<window>_b<width>.csv, plus a filtered
_cov<n>.csv export for count calibration. Neither is committed: both are
regenerable from the cache, and results/ is the source of truth. Until one
exists -- or when the one chosen holds nothing we can draw -- the map still
draws the corridor, coloured grey. We never invent a speed (CLAUDE.md rule 4).

TD's own incident times are drawn on the timeline when the loader's incident
table is there, and simply left off when it is not:

    python -m src.loaders.fetch incidents --start 2026-05-15 --end 2026-05-15

Run with:

    streamlit run src/console/app.py

Owner: Visuals.
"""
from __future__ import annotations

import glob
import os
import re
import time
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
# Tests point this at a fixture directory; everything else reads the real data/.
DATA_DIR = Path(os.environ.get("RIPPLE_DATA_DIR") or ROOT / "data")
DETECTORS_CSV = DATA_DIR / "detectors.csv"
SPEED_GLOB = str(DATA_DIR / "detector_5min_*.csv")
INCIDENT_GLOB = str(DATA_DIR / "incidents_*.csv")

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
# A loop that reported and counted nobody. On a closed link that is the
# incident, so it must not look like the grey of a missing reading.
NO_VEHICLES = [38, 38, 54]

# One series on the timeline, so it needs no legend -- the axis names it.
LINE_COLOUR = "#2a78d6"
EVENT_COLOUR = "#eb6834"
INK = "#52514e"

# How long one bin stays on screen while playing.
PLAY_PACES = {"1 bin/s": 1.0, "2 bins/s": 0.5, "4 bins/s": 0.25}


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


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    """A column as numbers, or all-NaN when the file does not carry it."""
    if column not in frame.columns:
        return pd.Series([float("nan")] * len(frame), index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce")


def load_speeds(path: str) -> pd.DataFrame:
    """Speeds per detector per bin, dropping blank speeds. Blank means no vehicle
    crossed the loop, not a speed of zero and not the speed limit -- see
    docs/02-data.md section 7. A quiet window can be blank throughout."""
    df = pd.read_csv(path)
    df = df[df["speed_kmh"] != ""]
    df["speed_kmh"] = pd.to_numeric(df["speed_kmh"], errors="coerce")
    return df.dropna(subset=["speed_kmh"])


def bin_state(frame: pd.DataFrame) -> pd.Series:
    """What each bin actually tells us. Three answers, none of them guessed:

    `speed`       the loop timed vehicles crossing it;
    `no_vehicles` the loop reported for this bin and counted none. An empty
                  road -- which on a closed link is the incident itself, and
                  is not the same thing as missing data;
    `unknown`     the archive served nothing for those minutes, or vehicles
                  were counted without a usable speed. Grey either way.

    The archive serves only about half the snapshots it lists, so the
    difference between "nobody drove past" and "we were not told" decides
    whether a dark map dot is evidence (docs/02-data.md section 7).
    """
    speed = _numeric(frame, "speed_kmh")
    periods = _numeric(frame, "periods_observed").fillna(0)
    volume = _numeric(frame, "volume_observed").fillna(0)
    state = pd.Series("unknown", index=frame.index)
    state[(periods > 0) & (volume == 0)] = "no_vehicles"
    state[speed.notna()] = "speed"
    return state


def load_bins(path: str) -> pd.DataFrame:
    """Every bin in the file, blanks kept.

    load_speeds() drops blank speeds because the map cannot colour them. The
    playback needs the blank rows too: without them a closed link disappears
    from the window instead of showing as closed.
    """
    frame = pd.read_csv(path)
    for column in ("speed_kmh", "volume_observed", "periods_observed",
                   "coverage_pct"):
        if column in frame.columns:
            frame[column] = _numeric(frame, column)
    frame["state"] = bin_state(frame)
    return frame


def showable_bins(frame: pd.DataFrame) -> list[str]:
    """Bins with something real to draw: a speed, or a loop reporting an empty
    road. A window with neither is one we cannot colour at all."""
    drawable = frame[frame["state"].isin(("speed", "no_vehicles"))]
    return sorted(drawable["bin_start"].unique())


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


def state_colour(state: str, speed: float | None) -> list[int]:
    """The ramp for a timed speed, its own dark dot for a road with no traffic
    on it, grey for a reading we do not have."""
    if state == "no_vehicles":
        return NO_VEHICLES
    return speed_to_colour(speed)


def state_label(state: str, speed: float | None) -> str:
    """What the dot claims, in words, so colour is never the only carrier."""
    if pd.notna(speed):
        return f"{speed:.0f} km/h"
    if state == "no_vehicles":
        return "no vehicle crossed"
    return "no reading"


def evidence_label(volume: float | None, coverage: float | None) -> str:
    """How thin the reading behind a dot is. A 65 km/h bin built from one
    vehicle is true and nearly meaningless; the tooltip has to say which."""
    parts = []
    if pd.notna(volume):
        count = int(volume)
        parts.append("1 vehicle" if count == 1 else f"{count} vehicles")
    if pd.notna(coverage):
        parts.append(f"{int(coverage)}% of the minutes")
    return " · ".join(parts)


# --- playback -------------------------------------------------------------

def next_index(index: int, n_bins: int) -> int | None:
    """The bin playback moves to next, or None at the end of the window.
    Playback stops at the end rather than looping: a demo that silently
    restarts makes the second pass look like new data."""
    return index + 1 if index + 1 < n_bins else None


def _window_key(bins: list[str]) -> str:
    return f"{bins[0]}|{bins[-1]}|{len(bins)}"


def playback_index(bins: list[str], width: int | None) -> int:
    """Draw the transport controls and return the bin to show.

    The index lives in session state so the buttons and the slider cannot
    disagree; picking a different snapshot rewinds to the start of it.
    """
    if st.session_state.get("window_key") != _window_key(bins):
        st.session_state.window_key = _window_key(bins)
        st.session_state.bin_index = 0
        st.session_state.playing = False
    index = min(st.session_state.get("bin_index", 0), len(bins) - 1)
    playing = st.session_state.get("playing", False)

    back, play, forward, rewind, _ = st.columns([1, 1, 1, 1, 6])
    if back.button("◀", help="one bin back", use_container_width=True):
        st.session_state.playing = playing = False
        index = max(0, index - 1)
    if play.button("⏸" if playing else "▶", help="play the window",
                   use_container_width=True):
        playing = not playing
        # Playing from the last bin would have nowhere to go: start again.
        if playing and index == len(bins) - 1:
            index = 0
        st.session_state.playing = playing
    if forward.button("▶|", help="one bin on", use_container_width=True):
        st.session_state.playing = playing = False
        index = min(len(bins) - 1, index + 1)
    if rewind.button("|◀", help="back to the start", use_container_width=True):
        st.session_state.playing = playing = False
        index = 0

    st.session_state.bin_index = index
    chosen = st.select_slider(
        f"{width}-minute bin" if width else "Time bin",
        options=bins, value=bins[index], format_func=label_bin)
    if chosen != bins[index]:
        # Scrubbing by hand takes over from playback.
        index = bins.index(chosen)
        st.session_state.bin_index = index
        st.session_state.playing = False
    return index


def autoplay_tick(n_bins: int, pace: float) -> None:
    """Hold the drawn frame for `pace` seconds, then step on and redraw.

    Called last, once the page is on screen, so the sleep is the frame's time
    rather than a delay before it appears.
    """
    if not st.session_state.get("playing"):
        return
    following = next_index(st.session_state.get("bin_index", 0), n_bins)
    if following is None:
        # End of the window: stop, but still redraw, or the button keeps
        # offering to pause something that has already stopped.
        st.session_state.playing = False
    else:
        time.sleep(pace)
        st.session_state.bin_index = following
    st.rerun()


# --- timeline -------------------------------------------------------------

def corridor_timeline(frame: pd.DataFrame) -> pd.DataFrame:
    """Per bin: the slowest detector that had a speed, and how much of the
    corridor was reporting.

    The corridor *mean* is deliberately not the series. Averaged over 28
    detectors in both directions it barely moves during a full closure of one
    link -- the queue is local, and a mean hides it.
    """
    rows = []
    for bin_start, group in frame.groupby("bin_start", sort=True):
        timed = group.dropna(subset=["speed_kmh"])
        slowest = timed.loc[timed["speed_kmh"].idxmin()] if not timed.empty else None
        rows.append({
            "bin_start": bin_start,
            "slowest_kmh": float(slowest["speed_kmh"]) if slowest is not None else None,
            "slowest_id": str(slowest["detector_id"]) if slowest is not None else "",
            "reporting": int(len(timed)),
            "no_vehicles": int((group["state"] == "no_vehicles").sum()),
        })
    return pd.DataFrame(rows)


def _as_local_time(values: pd.Series) -> pd.Series:
    """ISO timestamps to naive Hong Kong time, so the axis reads in clock time.
    Anything unparseable becomes NaT and is dropped by the caller."""
    parsed = pd.to_datetime(values, errors="coerce", utc=True)
    return parsed.dt.tz_convert("Asia/Hong_Kong").dt.tz_localize(None)


def load_incident_markers(first_bin: str, last_bin: str) -> pd.DataFrame:
    """TD's own times for corridor incidents inside the window, from the
    loader's incident table.

    Empty when that table has not been written. The console draws the times the
    archive recorded or none at all -- it never supplies one itself.
    """
    events = []
    for path in sorted(glob.glob(INCIDENT_GLOB)):
        table = pd.read_csv(path)
        if not {"corridor_road", "incident_number"} <= set(table.columns):
            continue
        on_corridor = table[table["corridor_road"].fillna("").astype(str) != ""]
        for _, row in on_corridor.iterrows():
            for column, said in (("new_at", "reported"), ("closed_at", "cleared")):
                when = str(row.get(column) or "")
                if when and first_bin <= when <= last_bin:
                    events.append({"bin_start": when,
                                   "label": f"{row['incident_number']} {said}"})
    return pd.DataFrame(events, columns=["bin_start", "label"])


def timeline_chart(timeline: pd.DataFrame, current_bin: str,
                   markers: pd.DataFrame) -> alt.LayerChart | None:
    """The window as a strip: slowest corridor speed per bin, where playback is
    up to, and what TD said when. None if the timestamps will not parse."""
    data = timeline.copy()
    data["t"] = _as_local_time(data["bin_start"])
    data = data.dropna(subset=["t"])
    if data.empty:
        return None

    axis_x = alt.Axis(format="%H:%M", grid=False, tickCount=8, title=None)
    axis_y = alt.Axis(grid=True, gridOpacity=0.15, tickCount=4, title="km/h")
    # Headroom above the line, so the incident labels do not sit on it. The
    # scale still starts at zero: a speed axis that does not would exaggerate
    # every dip on it.
    fastest = data["slowest_kmh"].max()
    top = float(fastest) * 1.3 if pd.notna(fastest) and fastest > 0 else None
    encode_xy = dict(
        x=alt.X("t:T", axis=axis_x),
        y=alt.Y("slowest_kmh:Q", axis=axis_y,
                scale=alt.Scale(domainMin=0, domainMax=top) if top
                else alt.Scale(domainMin=0)),
    )
    line = alt.Chart(data).mark_line(
        color=LINE_COLOUR, strokeWidth=2, interpolate="monotone").encode(**encode_xy)
    # Bigger than the mark, so hovering the line is not a pixel hunt.
    hover = alt.Chart(data).mark_circle(size=90, color=LINE_COLOUR, opacity=0.35).encode(
        tooltip=[alt.Tooltip("t:T", title="bin", format="%H:%M"),
                 alt.Tooltip("slowest_kmh:Q", title="slowest km/h", format=".0f"),
                 alt.Tooltip("slowest_id:N", title="detector"),
                 alt.Tooltip("reporting:Q", title="detectors with a speed"),
                 alt.Tooltip("no_vehicles:Q", title="loops reporting no vehicle")],
        **encode_xy)

    now = pd.DataFrame({"t": _as_local_time(pd.Series([current_bin]))}).dropna()
    layers = [line, hover]
    if not now.empty:
        layers.append(alt.Chart(now).mark_rule(color=INK, strokeWidth=2).encode(x="t:T"))

    if not markers.empty:
        events = markers.copy()
        events["t"] = _as_local_time(events["bin_start"])
        events = events.dropna(subset=["t"])
        if not events.empty:
            layers.append(alt.Chart(events).mark_rule(
                color=EVENT_COLOUR, strokeWidth=2, strokeDash=[4, 3]).encode(
                    x="t:T", tooltip=alt.Tooltip("label:N", title="TD")))
            layers.append(alt.Chart(events).mark_text(
                align="left", dx=4, dy=-4, fontSize=11, color=EVENT_COLOUR).encode(
                    x="t:T", y=alt.value(10), text="label:N"))

    return alt.layer(*layers).properties(
        height=170,
        title=alt.TitleParams("Slowest corridor detector, per bin",
                              anchor="start", fontSize=12, fontWeight="normal",
                              color=INK, offset=8))


# --- page -----------------------------------------------------------------

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
                "<div style='font-size:12px;color:#ccc'>{road_short}</div>"
                "<div style='font-size:11px;color:#999'>{evidence}</div>",
        "style": {"backgroundColor": "#111", "color": "white",
                  "padding": "6px 8px"},
    }
    # Carto's street basemap keeps roads visible at every zoom, no token needed.
    return pdk.Deck(layers=[dots], initial_view_state=view,
                    tooltip=tooltip, map_provider="carto", map_style="road")


def headline(detectors: pd.DataFrame) -> None:
    """A glanceable summary above the map."""
    known = detectors.dropna(subset=["speed_kmh"])
    empty = int((detectors["state"] == "no_vehicles").sum())
    c1, c2, c3, c4 = st.columns(4)
    if known.empty:
        c1.metric("Mean speed", "—")
        c2.metric("Slowest detector", "—")
        c3.metric("Congested detectors", "—")
    else:
        slowest = known.loc[known["speed_kmh"].idxmin()]
        congested = int((known["speed_kmh"] <= CONGESTED_KMH).sum())
        c1.metric("Mean corridor speed", f"{known['speed_kmh'].mean():.0f} km/h")
        c2.metric(f"Slowest · {slowest['detector_id']}",
                  f"{slowest['speed_kmh']:.0f} km/h",
                  help=slowest["road_en"])
        c3.metric(f"Congested (≤ {CONGESTED_KMH:.0f} km/h)",
                  f"{congested} of {len(known)}")
    c4.metric("Reporting no vehicle", f"{empty} of {len(detectors)}",
              help="The loop reported for this bin and counted nobody: an empty "
                   "road, not a missing reading.")


def colour_legend() -> None:
    st.markdown(
        "**Speed** &nbsp; "
        "<span style='color:#e00'>●</span> stopped &nbsp;&rarr;&nbsp; "
        "<span style='color:#e8a000'>●</span> slow &nbsp;&rarr;&nbsp; "
        f"<span style='color:#00b400'>●</span> free-flow "
        f"(≥ {FREE_FLOW_KMH:.0f} km/h) &nbsp;&middot;&nbsp; "
        "<span style='color:#262636'>●</span> no vehicle crossed "
        "&nbsp;&middot;&nbsp; "
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
    detectors["state"] = "unknown"
    detectors["volume_observed"] = None
    detectors["coverage_pct"] = None
    timeline, current_bin, n_bins = None, None, 0

    if not speed_files:
        st.info(
            "No speed snapshot found, so the corridor is grey. To colour by "
            "speed, ask the data layer for a window, e.g.\n\n"
            "`python -m src.loaders.fetch detectors "
            "--start 2026-05-15T07:55 --end 2026-05-15T10:35`"
        )
    else:
        chosen = st.sidebar.selectbox("Speed snapshot", speed_files,
                                      format_func=label_speed_file)
        pace = PLAY_PACES[st.sidebar.selectbox("Playback speed",
                                               list(PLAY_PACES), index=1)]
        frame = load_bins(chosen)
        bins = showable_bins(frame)
        if not bins:
            # Nothing to draw: no speed anywhere, and no loop reporting an
            # empty road either. Grey is the honest answer -- the same as
            # having no snapshot at all.
            st.info(
                f"`{Path(chosen).name}` carries no speed reading in any bin, so "
                "the corridor is grey. The data layer leaves speed blank when no "
                "vehicle crossed the loop (docs/02-data.md section 7), so a quiet "
                "window can be blank throughout. Pick another snapshot."
            )
        else:
            n_bins = len(bins)
            index = playback_index(bins, bin_minutes(frame))
            current_bin = bins[index]
            window = frame[frame["bin_start"] == current_bin].set_index("detector_id")
            for column in ("speed_kmh", "state", "volume_observed", "coverage_pct"):
                detectors[column] = detectors["detector_id"].map(window[column])
            detectors["state"] = detectors["state"].fillna("unknown")
            timeline = corridor_timeline(frame)

    detectors["colour"] = [state_colour(s, v) for s, v
                           in zip(detectors["state"], detectors["speed_kmh"])]
    detectors["speed_label"] = [state_label(s, v) for s, v
                                in zip(detectors["state"], detectors["speed_kmh"])]
    detectors["evidence"] = [evidence_label(v, c) for v, c
                             in zip(detectors["volume_observed"],
                                    detectors["coverage_pct"])]
    # The English name already ends in "- Eastbound"; drop it for a clean line.
    detectors["road_short"] = detectors["road_en"].str.split(" - ").str[0]

    headline(detectors)
    colour_legend()
    st.pydeck_chart(build_map(detectors))

    if timeline is not None and current_bin is not None:
        markers = load_incident_markers(timeline["bin_start"].iloc[0],
                                        timeline["bin_start"].iloc[-1])
        chart = timeline_chart(timeline, current_bin, markers)
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
        if markers.empty:
            st.caption(
                "No incident times drawn: run `python -m src.loaders.fetch "
                "incidents --start <day> --end <day>` to mark what TD said, and when."
            )

    st.caption(f"{len(detectors)} detectors · data: DATA.GOV.HK / Transport Department")

    if n_bins:
        autoplay_tick(n_bins, pace)


if __name__ == "__main__":
    main()
