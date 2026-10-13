"""Display Lead's checked retrospective candidates, without ranking or approval."""
import jsonschema
import streamlit as st

from scripts.build_genai_evidence import read_bundle


def show(root, message) -> None:
    st.subheader("Recorded Plan Generator drafts")
    if message is None or message.incident_id != "IN-26-03365":
        st.caption("This recorded example is for IN-26-03365. Select a bin after its first TD report.")
        return
    try:
        bundle = read_bundle(root)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError,
            AttributeError, jsonschema.ValidationError) as exc:
        st.warning(f"Recorded plan evidence unavailable: {exc}")
        return
    st.warning("Recorded GenAI draft — retrospective working assumptions; not evaluated.")
    st.caption("These candidates use the first 09:01 TD report and later-known incident details. "
               "They are a saved example, not new advice at the playback cursor.")
    st.caption("Incident P0 is not accepted. No plan ranking, recommended route or traffic benefit "
               "is established by these drafts.")
    call = bundle["d_call"]
    st.caption(f"Recorded {call['model']} call · {call['timestamp']}")
    for column, plan in zip(st.columns(3), bundle["plans"]):
        with column, st.container(border=True):
            st.markdown(f"**{plan['plan_id']} · {plan['label']}**")
            st.write(plan["rationale"])
            if not plan["diversions"]:
                st.caption("No diversion action.")
            for diversion in plan["diversions"]:
                st.markdown(f"**{diversion['od_group']}**")
                st.write(f"Via {diversion['via']}")
                st.caption(f"Advised share: {diversion['share']:.0%} · plan parameter")
            for signal in plan["signals"]:
                st.write(f"{signal['junction_id']}: +{signal['green_extend_s']} s green")
            if plan["plan_id"] == "P1":
                st.caption("Saved title says one OD group; its actions cover both groups. "
                           "Original model text is retained.")
            if plan["plan_id"] == "P2":
                st.caption("Signal control and timing are assumed network settings. "
                           "Real availability is unconfirmed.")
            with st.expander(f"Original {plan['plan_id']} JSON"):
                st.json(plan)
    with st.expander("Recorded draft sources"):
        st.text("data/generated-plans/IN-26-03365-lead-draft-20261013-b/\n"
                "data/plan-context/IN-26-03365_first-report-v2.json\n"
                "evidence/ai-log/2026-10-13.jsonl")
        st.caption("The exporter checks saved inputs, model replies and plan-file hashes. "
                   "Those checks establish evidence identity, not traffic-model validity.")
