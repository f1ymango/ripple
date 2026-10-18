"""Tuen Mun case view for Ripple's operator console.

The map and playback use TD observations. The plan chart uses the frozen SUMO
comparison. They are deliberately labelled separately so a recorded speed is
never presented as a simulated outcome or vice versa.
"""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.console import tuen_mun_data, tuen_mun_geometry


ROOT = Path(__file__).resolve().parents[2]
OBSERVATIONS = ROOT / "sim" / "tuen-mun" / "observations_20260415.json"
PLACEMENTS = ROOT / "sim" / "tuen-mun" / "detectors-placement.json"
NETWORK = ROOT / "sim" / "tuen-mun" / "network.net.xml"
FIRST_REPORT = ROOT / "data" / "lead-inputs" / "IN-26-02615_first-report.json"
DEMO_PACK = ROOT / "results" / "demo-oct16" / "tuen-mun"
VERDICT = DEMO_PACK / "verdict.json"
RANKING = DEMO_PACK / "rankings" / "lead-capacity-oct15.json"
PLAN_P2 = DEMO_PACK / "plans" / "P2.json"

# TD's 18:46 reopening report is recorded in docs/tuen-mun-2026-10-14.md.
# It is a report time, not an inferred physical reopening timestamp.
REOPENING_REPORT = "2026-04-15T18:46:00+08:00"


def incident_markers(first_report: dict) -> pd.DataFrame:
    """The two TD report times used on the archived-observation timeline."""
    return pd.DataFrame([
        {"bin_start": first_report["announced_at"],
         "label": "TD first report · 17:59", "incident_id": first_report["incident_id"],
         "kind": "report"},
        {"bin_start": REOPENING_REPORT,
         "label": "TD reopening report · 18:46",
         "incident_id": first_report["incident_id"], "kind": "clearance"},
    ])


def load_plan_evidence() -> dict:
    """Read and cross-check the frozen case summary, rank, and proposed plan."""
    verdict = json.loads(VERDICT.read_text(encoding="utf-8"))
    ranking = json.loads(RANKING.read_text(encoding="utf-8"))
    plan = json.loads(PLAN_P2.read_text(encoding="utf-8"))
    if (verdict.get("incident_id") != "IN-26-02615"
            or ranking.get("incident_id") != verdict["incident_id"]
            or verdict.get("plan_set") != ranking.get("plan_set")
            or verdict.get("console_recommends") != ranking.get("first")
            or ranking.get("first") != plan.get("plan_id")):
        raise ValueError("Tuen Mun frozen plan evidence does not agree.")
    pairs = {(p["a"], p["b"]): p for p in ranking["pairs"]}
    p0_p2 = pairs[("P0", "P2")]
    p0_p1 = pairs[("P0", "P1")]
    if not (p0_p2["before"] == "P2" and p0_p1["before"] == "P0"
            and p0_p2["cells"] == p0_p1["cells"]):
        raise ValueError("Tuen Mun frozen ranking has changed.")
    diversion = next((d for d in plan["diversions"]
                      if d.get("via") == "Castle Peak Road"), None)
    if diversion is None:
        raise ValueError("Frozen Tuen Mun P2 has no Castle Peak Road diversion.")
    return {"verdict": verdict, "ranking": ranking, "plan": plan,
            "p0_p2": p0_p2, "p0_p1": p0_p1,
            "diversion_share": float(diversion["share"])}


def _detector_headline(detectors: pd.DataFrame) -> None:
    """Four glanceable measures drawn only from the selected TD time bin."""
    known = detectors.dropna(subset=["speed_kmh"])
    c1, c2, c3, c4 = st.columns(4)
    if known.empty:
        c1.metric("Mean observed speed", "—")
        c2.metric("Slowest detector", "—")
        c3.metric("≤ 30 km/h", "—")
    else:
        slowest = known.loc[known["speed_kmh"].idxmin()]
        c1.metric("Mean observed speed", f"{known['speed_kmh'].mean():.0f} km/h")
        c2.metric(f"Slowest · {slowest['detector_id']}",
                  f"{slowest['speed_kmh']:.0f} km/h", help=slowest["road_en"])
        c3.metric("≤ 30 km/h", f"{int((known['speed_kmh'] <= 30).sum())} of {len(known)}")
    c4.metric("Speed readings", f"{len(known)} of {len(detectors)}",
              help="A missing TD speed reading is not interpreted as a stopped car or an empty road.")


def _speed_legend(console) -> None:
    st.markdown(
        "**TD detector speed** &nbsp; "
        "<span style='color:#e00'>●</span> stopped &nbsp;→&nbsp; "
        "<span style='color:#e8a000'>●</span> slow &nbsp;→&nbsp; "
        f"<span style='color:#00b400'>●</span> ≥ {console.FREE_FLOW_KMH:.0f} km/h "
        "&nbsp;·&nbsp; <span style='color:#a0a0a0'>●</span> no reading",
        unsafe_allow_html=True,
    )


def _incident_card(first_report: dict, current_bin: str) -> None:
    st.subheader("Incident signal")
    current = pd.Timestamp(current_bin)
    announced = pd.Timestamp(first_report["announced_at"])
    reopened = pd.Timestamp(REOPENING_REPORT)
    with st.container(border=True):
        st.markdown("**IN-26-02615 · Tuen Mun Road**")
        st.caption("Near Hong Kong Garden · Tuen Mun bound")
        if current < announced:
            st.info("Playback is before TD's first report at 17:59 HKT.")
        elif current < reopened:
            st.warning("TD reported lane closure at 17:59 HKT · one lane remaining.")
        else:
            st.success("TD reported reopening at 18:46 HKT.")
        with st.expander("TD first-report text and source"):
            st.write(first_report["source_message_en"])
            st.write(first_report["source_message_zh"])
            st.caption("TD first-report transcription from the frozen Lead input; "
                       "this is not a generated Reader output. "
                       "No exact crash coordinates were supplied.")


def _speed_heatmap(bins: pd.DataFrame, detectors: pd.DataFrame) -> alt.Chart:
    """Observed speed across all detectors and bins; missing cells stay grey."""
    ordered = detectors["detector_id"].tolist()
    frame = bins[["detector_id", "bin_start", "speed_kmh"]].copy()
    frame["time"] = pd.to_datetime(frame["bin_start"], utc=True).dt.tz_convert(
        "Asia/Hong_Kong").dt.tz_localize(None)
    axes = dict(x=alt.X("time:T", axis=alt.Axis(format="%H:%M", title="15 Apr · HKT")),
                y=alt.Y("detector_id:N", sort=ordered,
                        axis=alt.Axis(title="TD detector · east to west")))
    background = alt.Chart(frame).mark_rect(color="#a0a0a0").encode(**axes)
    measured = alt.Chart(frame.dropna(subset=["speed_kmh"])).mark_rect().encode(
        **axes,
        color=alt.Color("speed_kmh:Q", title="km/h",
                        scale=alt.Scale(domain=[0, 100], scheme="redyellowgreen")),
        tooltip=[alt.Tooltip("detector_id:N", title="Detector"),
                 alt.Tooltip("time:T", title="HKT", format="%H:%M"),
                 alt.Tooltip("speed_kmh:Q", title="Observed km/h", format=".0f")],
    )
    return alt.layer(background, measured).properties(height=470)


def _plan_panel(evidence: dict) -> None:
    verdict = evidence["verdict"]
    p0_p2 = evidence["p0_p2"]
    p0_p1 = evidence["p0_p1"]
    share = evidence["diversion_share"]
    cells = p0_p2["cells"]
    st.subheader("The operator choice · frozen SUMO comparison")
    st.success(f"Recommended for operator review: P2 · {evidence['plan']['label']}")
    lead, support = st.columns([1, 2])
    with lead:
        st.metric("Targeted advice vs no advice",
                  f"−{p0_p2['mean_difference_pct']:.1f}%",
                  help=f"Paired simulated total-delay difference across {cells} counting model conditions.")
        st.markdown(f"**P2 · advise {share:.0%}** of eligible Tuen Mun-bound "
                    "drivers to use Castle Peak Road")
        st.caption(f"Ranks ahead of P0 and P1 across {cells} paired model "
                   "conditions. Blanket advice (P1) raised modelled delay "
                   f"{abs(p0_p1['mean_difference_pct']):.1f}% against P0 on average.")
    with support:
        values = verdict["simulated_total_delay_vehicle_hours"]
        chart_data = pd.DataFrame([
            {"plan": "P2 · targeted", "delay": values["P2"], "colour": "#0c9c75"},
            {"plan": "P0 · no advice", "delay": values["P0"], "colour": "#477fbb"},
            {"plan": "P1 · blanket", "delay": values["P1"], "colour": "#d58648"},
        ])
        chart = alt.Chart(chart_data).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X("delay:Q", title="Simulated total delay · vehicle-hours",
                    scale=alt.Scale(domain=[0, max(values.values()) * 1.15])),
            y=alt.Y("plan:N", sort=["P2 · targeted", "P0 · no advice", "P1 · blanket"],
                    title=None),
            color=alt.Color("colour:N", scale=None, legend=None),
            tooltip=[alt.Tooltip("plan:N"), alt.Tooltip("delay:Q", format=",.1f")],
        ).properties(height=160)
        labels = alt.Chart(chart_data).mark_text(align="left", dx=5).encode(
            x="delay:Q", y=alt.Y("plan:N", sort=["P2 · targeted", "P0 · no advice",
                                             "P1 · blanket"]),
            text=alt.Text("delay:Q", format=",.1f"),
        )
        st.altair_chart(chart + labels, use_container_width=True)
        cell = verdict["cell"]
        st.caption(f"One matched display cell: {cell['compliance']:.0%} compliance, "
                   f"seed {cell['seed']}, {cell['clearance_min']:.0f} min clearance. "
                   "The −4.3% headline is the paired 18-condition ranking, not this one cell.")
    st.caption("Modelled comparison; observed queue was slower and lasted longer than the replay. "
               "These are simulated candidate outcomes, not measured road savings.")


def render(console) -> None:
    """Render the Tuen Mun incident case inside the shared Streamlit app."""
    st.title("Ripple — Tuen Mun Road")
    st.caption("Operator console · 15 April 2026 evening peak · TD observations + frozen plan study")
    try:
        detectors, frame = tuen_mun_data.load_playback(OBSERVATIONS, PLACEMENTS)
        first_report = json.loads(FIRST_REPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        st.error(f"Tuen Mun archived observations unavailable: {exc}")
        return

    pace = console.PLAY_PACES[st.sidebar.selectbox(
        "Playback speed", list(console.PLAY_PACES), index=1, key="tuen_pace")]
    bins = console.showable_bins(frame)
    if not bins:
        st.info("This TD observation window has no measured speed to draw.")
        return
    index = console.playback_index(bins, console.bin_minutes(frame))
    current_bin = bins[index]
    window = frame[frame["bin_start"] == current_bin].set_index("detector_id")
    for column in ("speed_kmh", "state", "volume_observed", "coverage_pct"):
        detectors[column] = detectors["detector_id"].map(window[column])
    detectors["state"] = detectors["state"].fillna("unknown")
    detectors["colour"] = [console.state_colour(s, v) for s, v
                           in zip(detectors["state"], detectors["speed_kmh"])]
    detectors["speed_label"] = [console.state_label(s, v) for s, v
                                in zip(detectors["state"], detectors["speed_kmh"])]
    detectors["evidence"] = [console.evidence_label(v, c) for v, c
                             in zip(detectors["volume_observed"], detectors["coverage_pct"])]
    detectors["road_short"] = detectors["road_en"].str.split(" - ").str[0]

    selected_time = pd.Timestamp(current_bin).tz_convert("Asia/Hong_Kong")
    st.markdown(f"**Archived TD observations · {selected_time:%d %b %Y · %H:%M} HKT**")
    st.caption("Map and timeline show recorded five-minute detector speeds. Grey means no speed reading.")
    _detector_headline(detectors)
    _speed_legend(console)

    roads = []
    if st.sidebar.checkbox("Show road network", value=True, key="tuen_roads"):
        try:
            roads = tuen_mun_geometry.load_overlay(NETWORK)
        except (OSError, ValueError, KeyError) as exc:
            st.sidebar.warning(f"Road geometry unavailable: {exc}")
    if roads:
        st.caption("Blue: Tuen Mun Road · purple: Castle Peak Road. "
                   "Network geometry only; not a validated diversion route. "
                   "Map shapes: OpenStreetMap contributors / SUMO.")

    map_col, report_col = st.columns([2.2, 1])
    with map_col:
        st.pydeck_chart(console.build_map(detectors, roads))
    with report_col:
        _incident_card(first_report, current_bin)

    timeline = console.corridor_timeline(frame)
    markers = incident_markers(first_report)
    st.caption("Observed slowest detector per five-minute bin · orange lines are TD report times.")
    chart = console.timeline_chart(timeline, current_bin, markers)
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    with st.expander("Explore all 27 detector speeds across the window"):
        st.altair_chart(_speed_heatmap(frame, detectors), use_container_width=True)
        st.caption("Grey cells have no measured speed. Detector order follows the TD corridor list.")

    st.caption(f"{len(detectors)} westbound TD detectors · source: DATA.GOV.HK / Transport Department")
    try:
        evidence = load_plan_evidence()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        st.warning(f"Frozen plan comparison unavailable: {exc}")
    else:
        _plan_panel(evidence)

    console.autoplay_tick(len(bins), pace)
