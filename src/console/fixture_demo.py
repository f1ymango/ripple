"""Isolated, visibly synthetic approval rehearsal. No LLM or simulator calls.

Run: streamlit run src/console/fixture_demo.py --server.port 8505
All copied inputs and audit output stay under tests/fixtures/mock_operator_capture/.
"""
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from src.console import app

FIXTURES = ROOT / "tests" / "fixtures" / "mock_recommendation"
CAPTURE = ROOT / "tests" / "fixtures" / "mock_operator_capture"


def prepare() -> tuple[Path, Path, Path, Path]:
    """Copy the existing test fixtures verbatim; preserve any prior mock audit."""
    results, plans, briefings = [CAPTURE / name for name in ("runs", "plans", "briefings")]
    for directory in (results, plans, briefings):
        directory.mkdir(parents=True, exist_ok=True)
    for source in FIXTURES.glob("mock_p*.json"):
        target = (results if "_result" in source.name else plans) / source.name
        if not target.exists():
            shutil.copyfile(source, target)
    for source, target in (
        (FIXTURES / "mock_generation-inputs.json", plans / "generation-inputs.json"),
        (FIXTURES / "mock_briefing.json", briefings / "mock_briefing.json"),
    ):
        if not target.exists():
            shutil.copyfile(source, target)
    return results, plans, briefings, CAPTURE / "mock_audit_log.jsonl"


def main() -> None:
    st.set_page_config(page_title="Ripple — synthetic approval rehearsal", layout="wide")
    st.markdown("""<style>
      .block-container {padding-top: 1.5rem;}
      h1 {font-size: 2rem;}
      .fixture-badge {position: fixed; top: 64px; right: 80px; z-index: 9999;
        background: #572777; color: white; padding: 8px 14px; border-radius: 6px;}
    </style><div class="fixture-badge">SYNTHETIC FIXTURE · No incident benefit claims</div>""",
                unsafe_allow_html=True)
    st.title("Ripple — approval rehearsal")
    st.warning("Synthetic test fixture. Every plan, figure and briefing here is mock. "
               "This demonstrates the review controls; it is not an incident recommendation.")
    results, plans, briefings, audit = prepare()
    with st.expander("Synthetic comparison inputs"):
        comparison = app.show_plan_comparison(results, plans)
    app.show_operator_briefing(comparison, results_dir=results, plans_dir=plans,
                              briefings_dir=briefings, audit_path=audit)
    if audit.exists():
        try:
            records = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()
                       if line.strip()]
        except (OSError, ValueError) as exc:
            st.error(f"Cannot read the mock audit: {exc}")
            return
        st.subheader("Mock audit trail")
        st.table([{key: row[key] for key in ("action", "operator", "incident_id", "plan_id")}
                  for row in records[-5:]])
        with st.expander("Mock audit records and evidence hashes"):
            st.json(records[-5:])
        st.caption("Written only to tests/fixtures/mock_operator_capture/mock_audit_log.jsonl")


if __name__ == "__main__":
    main()
