"""Label the gold set by hand: one STN message at a time, each answer saved as you go.

    streamlit run src/reader/label.py

Shows one message in both languages, the feed's own hint fields, and a form
for the fields the Incident Reader extracts. It never shows the Reader's
output: a label is your own reading of the message, not a check of the model's.
The rules for each field are in data/labelled_incidents/LABELLING.md.
"""
import sys
from pathlib import Path

import jsonschema
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # `streamlit run` does not add the repo root
from src.reader import gold, reader  # noqa: E402

TYPES = reader.SCHEMA["properties"]["incident_type"]["enum"]
LANES = reader.SCHEMA["properties"]["lanes_closed"]["items"]["enum"]
HINT_FIELDS = ["INCIDENT_HEADING", "INCIDENT_DETAIL", "LOCATION", "DIRECTION",
               "NEAR_LANDMARK", "BETWEEN_LANDMARK", "DISTRICT"]

st.set_page_config(page_title="Gold-set labelling", layout="wide")

if not gold.MESSAGES_PATH.exists():
    st.error(f"No gold messages yet: {gold.MESSAGES_PATH} is missing. "
             "See data/labelled_incidents/LABELLING.md, step 1.")
    st.stop()
messages = gold.load_messages(gold.MESSAGES_PATH)
try:
    labels = gold.load_labels(gold.LABELS_PATH)
except ValueError as exc:
    st.error(f"The labels file has a problem, fix it by hand first: {exc}")
    st.stop()

if "position" not in st.session_state:  # start at the first message not labelled yet
    st.session_state.position = next((i + 1 for i, m in enumerate(messages)
                                      if m["stn"]["ID"] not in labels), 1)


def save(message: dict) -> None:
    """Form callback: validate and write the label, then move on to the next message."""
    mid = message["stn"]["ID"]
    form = {field: st.session_state[f"{field}:{mid}"]
            for field in gold.SCORED_FIELDS + ["unsure", "comment"]}
    label = {"message_id": mid, "incident_id": message["stn"]["INCIDENT_NUMBER"]}
    label |= {field: form[field].strip() or None for field in gold.TEXT_FIELDS}
    label["incident_type"] = form["incident_type"]
    label["lanes_closed"] = [lane for lane in LANES if lane in form["lanes_closed"]]
    total = form["lanes_total"].strip()
    label["lanes_total"] = int(total) if total.isdigit() else total or None
    label["unsure"] = form["unsure"]
    label["comment"] = form["comment"].strip()
    if label["incident_type"] is None:
        st.session_state.problem = "Pick an incident type."
        return
    if isinstance(label["lanes_total"], str):
        st.session_state.problem = f"lanes_total must be a whole number or blank, not {total!r}."
        return
    try:
        gold.validate(label)
    except (ValueError, jsonschema.ValidationError) as exc:
        st.session_state.problem = str(exc).splitlines()[0]
        return
    saved = gold.load_labels(gold.LABELS_PATH)
    saved[mid] = label
    gold.save_labels(saved, messages, gold.LABELS_PATH)
    st.session_state.problem = None
    st.session_state.position = min(st.session_state.position + 1, len(messages))


with st.sidebar:
    st.header("Gold set")
    done = sum(m["stn"]["ID"] in labels for m in messages)
    st.progress(done / len(messages), text=f"{done} of {len(messages)} labelled")
    for stratum in ("citywide", "corridor"):
        in_stratum = [m for m in messages if m.get("stratum") == stratum]
        if in_stratum:
            st.caption(f"{stratum}: {sum(m['stn']['ID'] in labels for m in in_stratum)} "
                       f"of {len(in_stratum)}")
    unsure = [label["message_id"] for label in labels.values() if label["unsure"]]
    st.caption(f"marked unsure: {len(unsure)}")
    st.number_input("Message", min_value=1, max_value=len(messages), step=1, key="position",
                    on_change=lambda: st.session_state.update(problem=None))
    st.caption("Rules: data/labelled_incidents/LABELLING.md")

message = messages[st.session_state.position - 1]
stn, mid = message["stn"], message["stn"]["ID"]
existing = labels.get(mid)

st.subheader(f"Message {mid} · {stn['INCIDENT_NUMBER']} · {stn['INCIDENT_STATUS_EN']}"
             + (" · ✅ labelled" if existing else ""))
st.caption(f"announced {stn['ANNOUNCEMENT_DATE']} · stratum: {message.get('stratum', '-')}")
left, right = st.columns(2)
left.markdown("**English**")
left.info(stn["CONTENT_EN"] or "(empty)")
right.markdown("**中文**")
right.info(stn["CONTENT_CN"] or "(empty)")
with st.expander("The feed's hint fields (sometimes empty or generic: the message text wins)"):
    st.table({field: {"EN": stn.get(f"{field}_EN", ""), "中文": stn.get(f"{field}_CN", "")}
              for field in HINT_FIELDS})

if st.session_state.get("problem"):
    st.error(st.session_state.problem)

with st.form(f"label:{mid}", enter_to_submit=False):
    a, b = st.columns(2)
    for column, field, help_text in [
        (a, "road_name", "Official English name as written, with any section bracket. "
                          "Blank = the message names no road."),
        (a, "direction", "'<place> bound', or 'both directions'. Blank = not stated."),
        (b, "near_landmark", "Blank = none stated."),
        (b, "between_landmark", "'X and Y'. Blank = the message does not say 'between'."),
    ]:
        column.text_input(field, value=(existing or {}).get(field) or "", help=help_text,
                          key=f"{field}:{mid}")
    c, d, e = st.columns([2, 3, 1])
    c.selectbox("incident_type", TYPES, key=f"incident_type:{mid}",
                index=TYPES.index(existing["incident_type"]) if existing else None)
    d.multiselect("lanes_closed", LANES, default=existing["lanes_closed"] if existing else [],
                  help="Lanes closed AS OF this message. Re-opened = empty, even if a lane is named. "
                       "'unspecified' = closed, but not which.",
                  key=f"lanes_closed:{mid}")
    # A text box, not a number box: once a number box holds a saved value it cannot be emptied again.
    e.text_input("lanes_total", key=f"lanes_total:{mid}",
                 value=str(existing["lanes_total"]) if existing and existing["lanes_total"] else "",
                 help="Only if the message states it. Blank = not stated.")
    st.checkbox("unsure", value=existing["unsure"] if existing else False, key=f"unsure:{mid}")
    st.text_area("comment (never scored)", value=existing["comment"] if existing else "",
                 key=f"comment:{mid}", height=68)
    st.form_submit_button("Save and next", type="primary", on_click=save, args=(message,))
