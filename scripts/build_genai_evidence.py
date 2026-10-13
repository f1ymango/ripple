"""Build a portable B/D evidence page from recorded, checked source files.

Rendering uses the standard library and the existing plan validator. No model,
simulator, network service or new package is required.
"""

import argparse
from datetime import date
import hashlib
from html import escape
import json
from pathlib import Path

from src.plans.generator import validate_plans
from src.reader.reader import INPUT_FIELDS, assemble


ROOT = Path(__file__).resolve().parents[1]
MESSAGE_IDS = ("138270", "138272")
READER_CALLS = {
    "138270": "2026-09-29T16:08:50+08:00",
    "138272": "2026-09-29T16:09:33+08:00",
}
PLAN_CALL = "2026-10-13T12:20:13+08:00"
PLAN_DIR = "data/generated-plans/IN-26-03365-lead-draft-20261013-b"
SOURCES = {
    "TD source messages": "data/demo_incident_messages.jsonl",
    "Saved Reader output": "results/reader/2026-09-29T1608_qwen3-8b.jsonl",
    "Reader call log": "evidence/ai-log/2026-09-29.jsonl",
    "Reviewed context (working assumptions)": "data/plan-context/IN-26-03365_first-report-v2.json",
    "Context qualifications": "data/plan-context/IN-26-03365_first-report-v2.md",
    "D generation inputs": f"{PLAN_DIR}/generation-inputs.json",
    "P0 candidate": f"{PLAN_DIR}/P0.json",
    "P1 candidate": f"{PLAN_DIR}/P1.json",
    "P2 candidate": f"{PLAN_DIR}/P2.json",
    "D call log": "evidence/ai-log/2026-10-13.jsonl",
    "Lead handoff and qualifications": "docs/lead-genai-handoff-2026-10-13.md",
}
EXPECTED_PLAN_HASHES = {
    "P0 candidate": "4198ec674296e0a1413b3ef3d0758fdf3e60124afbe9d51728b912b69ed898ff",
    "P1 candidate": "dae8a9c06f0e7d34b77407193ff36eb1d814311b8a8d0739fe508190da27dade",
    "P2 candidate": "3afc8b638a7abd2d9a290541d07032ab9a9f269fa4196c14f479ef7284eea20c",
    "D generation inputs": "8726acd9be7023a9483f3e46128fa172abb6bebf5f1361970194144d904f33a1",
}


def exact_one(rows, predicate, label):
    matches = [row for row in rows if predicate(row)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {label}; found {len(matches)}")
    return matches[0]


def read_jsonl(data):
    return [json.loads(line) for line in data.decode("utf-8").splitlines()
            if line.strip()]


def read_bundle(root=ROOT):
    """Check every selected record, response and saved plan before rendering."""
    paths = {label: root / relative for label, relative in SOURCES.items()}
    source_bytes = {label: path.read_bytes() for label, path in paths.items()}
    hashes = {label: hashlib.sha256(data).hexdigest()
              for label, data in source_bytes.items()}
    for label, expected in EXPECTED_PLAN_HASHES.items():
        if hashes[label] != expected:
            raise ValueError(f"{label} changed since the reviewed handoff")

    raw_rows = read_jsonl(source_bytes["TD source messages"])
    reader_rows = read_jsonl(source_bytes["Saved Reader output"])
    reader_logs = read_jsonl(source_bytes["Reader call log"])
    messages = []
    for message_id in MESSAGE_IDS:
        raw = exact_one(raw_rows, lambda row: row.get("stn", {}).get("ID") == message_id,
                        f"source message {message_id}")
        parsed = exact_one(reader_rows, lambda row: row.get("message_id") == message_id,
                           f"Reader output {message_id}")
        call = exact_one(reader_logs,
                         lambda row: row.get("timestamp") == READER_CALLS[message_id]
                         and row.get("component") == "reader",
                         f"Reader call {READER_CALLS[message_id]}")
        if call.get("model") != "qwen3:8b" or call.get("error"):
            raise ValueError(f"Reader call {message_id} has unexpected model or error")
        expected_user = {field: raw["stn"][field] for field in INPUT_FIELDS}
        if json.loads(call["user"]) != expected_user:
            raise ValueError(f"Reader call {message_id} does not match its source message")
        if parsed.get("incident") != assemble(raw["stn"], json.loads(call["response"])):
            raise ValueError(f"Saved Reader output {message_id} differs from its call")
        messages.append({"id": message_id, "raw": raw, "parsed": parsed,
                         "call": call})

    inputs = json.loads(source_bytes["D generation inputs"])
    context = json.loads(source_bytes["Reviewed context (working assumptions)"])
    if inputs.get("incident") != messages[0]["parsed"]["incident"] or inputs.get("policy_context") != context:
        raise ValueError("D inputs differ from the selected B output or reviewed context")
    plan_logs = read_jsonl(source_bytes["D call log"])
    call = exact_one(plan_logs,
                     lambda row: row.get("timestamp") == PLAN_CALL and row.get("component") == "plans",
                     f"D call {PLAN_CALL}")
    if call.get("model") != "qwen3:8b" or call.get("error"):
        raise ValueError("D call has unexpected model or error")
    if json.loads(call["user"])["input"] != inputs:
        raise ValueError("D call input differs from saved generation inputs")
    generated = json.loads(call["response"])
    checked = validate_plans(generated, context, inputs["incident"])
    plans = [json.loads(source_bytes[f"{plan_id} candidate"])
             for plan_id in ("P0", "P1", "P2")]
    if checked != plans:
        raise ValueError("Saved candidate actions/text differ from the validated D response")
    if (plans[1]["label"] != "Single OD Group Detour"
            or len({item["od_group"] for item in plans[1]["diversions"]}) != 2
            or context["signals"].get("Wong Chuk Hang Road / Tong Bin Lane") != 20):
        raise ValueError("Known P1 title and assumed-signal qualifications changed")
    return {"messages": messages, "inputs": inputs, "plans": plans,
            "d_call": call, "hashes": hashes}


def h(value):
    return escape(str(value), quote=True)


def field(label, value):
    return f'<div class="field"><dt>{h(label)}</dt><dd>{h(value)}</dd></div>'


def message_html(item):
    raw = item["raw"]["stn"]
    incident = item["parsed"]["incident"]
    lanes = ", ".join(incident["lanes_closed"]) or "none"
    note = ("The saved first note overdescribes the direction: the TD feed has a separate "
            "direction field. It is retained as model output, not evidence of a road-name bracket."
            if item["id"] == "138270" else "The later update explicitly reports all lanes closed.")
    extracted = "".join((
        field("Road", incident["road_name"]), field("Direction", incident["direction"]),
        field("Landmark", incident["near_landmark"]), field("Lanes closed", lanes),
        field("Incident type", incident["incident_type"]),
        field("Model confidence (self reported)", incident["confidence"]),
        field("Saved model note", incident["notes"]),
    ))
    return f"""
      <section class="message">
        <div class="section-kicker">TD message {h(item['id'])} · {h(raw['ANNOUNCEMENT_DATE'])} HKT</div>
        <div class="pair">
          <article class="card">
            <h3>Archived bilingual message</h3>
            <p class="source-text" lang="en">{h(raw['CONTENT_EN'])}</p>
            <p class="source-text zh" lang="zh-Hant">{h(raw['CONTENT_CN'])}</p>
          </article>
          <article class="card">
            <h3>Saved Reader extraction</h3>
            <dl>{extracted}</dl>
            <p class="caution">{h(note)}</p>
          </article>
        </div>
        <p class="trace">Recorded Qwen3:8b call: {h(item['call']['timestamp'])}. This is one saved example, not an accuracy score.</p>
      </section>"""


def plan_html(plan):
    plan_id = plan["plan_id"]
    if plan_id == "P0":
        actions = "No diversion, signal, sign or public transport action. Comparison baseline only."
    else:
        actions = "".join(
            f"<li>{h(item['od_group'])} via {h(item['via'])}: "
            f"{h(round(item['share'] * 100))}% advised diversion share</li>"
            for item in plan["diversions"])
        actions = f"<ul>{actions}</ul>"
        if plan["signals"]:
            actions += "<p>Proposed signal setting: " + "; ".join(
                f"{h(item['junction_id'])}, +{h(item['green_extend_s'])} s green"
                for item in plan["signals"]) + "</p>"
        actions += "<p>No sign or public transport action in this saved plan.</p>"
    special = ""
    if plan_id == "P1":
        special = ('<p class="caution">Original title says “Single OD Group,” while the saved actions '
                   'cover both supplied groups. The original model text is preserved.</p>')
    elif plan_id == "P2":
        special = ('<p class="caution">The Tong Bin Lane control and 20 s limit are working '
                   'network assumptions; real signal availability and timing are unconfirmed.</p>')
    return f"""
      <article class="card plan">
        <div class="plan-id">{h(plan_id)}</div>
        <h3>{h(plan['label'])}</h3>
        <p>{h(plan['rationale'])}</p>
        {actions}{special}
      </article>"""


def render(bundle, capture_date):
    """Return one offline page; every value from a source file is escaped."""
    date.fromisoformat(capture_date)
    context = bundle["inputs"]["policy_context"]
    source_rows = "".join(
        f"<tr><th>{h(label)}</th><td><code>{h(relative)}</code></td>"
        f"<td><code>{h(bundle['hashes'][label])}</code></td></tr>"
        for label, relative in SOURCES.items())
    messages = "".join(message_html(item) for item in bundle["messages"])
    plans = "".join(plan_html(plan) for plan in bundle["plans"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Ripple · recorded B/D GenAI evidence</title>
  <style>
    :root {{ font-family: system-ui, 'Segoe UI', sans-serif; color: #172532; background: #f2f5f5; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; line-height: 1.52; }}
    .banner {{ position: sticky; top: 0; z-index: 3; padding: .68rem 1.3rem; background: #153646; color: #fff; font-size: .92rem; font-weight: 700; letter-spacing: .01em; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 1.3rem 1.3rem 3rem; }}
    .mast {{ border-left: 6px solid #15877e; padding: .4rem 1.15rem 1rem; margin: 1rem 0 2rem; }}
    h1 {{ font-size: clamp(1.65rem, 3vw, 2.5rem); line-height: 1.16; margin: .35rem 0; }}
    h2 {{ font-size: 1.35rem; margin: 0 0 .65rem; }}
    h3 {{ font-size: 1.03rem; margin: 0 0 .75rem; }}
    p {{ margin: .55rem 0; }}
    .eyebrow, .section-kicker, .plan-id {{ color: #167268; font-size: .83rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
    .section {{ margin: 2rem 0; }}
    .message {{ margin: 1.35rem 0 2rem; }}
    .pair {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: .55rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }}
    .card {{ padding: 1.15rem 1.2rem; border: 1px solid #d9e2e2; border-radius: 12px; background: #fff; box-shadow: 0 3px 12px #1737470a; min-width: 0; }}
    .source-text {{ padding: .7rem .85rem; border-left: 3px solid #8cc4bd; background: #f3f8f7; overflow-wrap: anywhere; }}
    .zh {{ font-family: 'Microsoft JhengHei', 'Noto Sans CJK TC', system-ui, sans-serif; line-height: 1.8; }}
    dl {{ margin: 0; }}
    .field {{ display: grid; grid-template-columns: minmax(8.2rem, 37%) 1fr; gap: .6rem; border-top: 1px solid #e4ebeb; padding: .42rem 0; overflow-wrap: anywhere; }}
    dt {{ color: #526775; font-size: .9rem; }}
    dd {{ margin: 0; font-weight: 600; }}
    .caution {{ border-left: 3px solid #c17724; background: #fff6eb; color: #62410e; padding: .6rem .8rem; font-size: .92rem; }}
    .trace, .subtle {{ color: #556b77; font-size: .9rem; }}
    .plan ul {{ padding-left: 1.1rem; }}
    .plan li {{ margin: .45rem 0; }}
    .qualifications {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
    .source-table {{ overflow-x: auto; border: 1px solid #d9e2e2; border-radius: 10px; background: #fff; }}
    table {{ border-collapse: collapse; width: 100%; text-align: left; font-size: .82rem; }}
    th, td {{ padding: .6rem .7rem; border-bottom: 1px solid #e4ebeb; vertical-align: top; }}
    td code {{ overflow-wrap: anywhere; word-break: break-word; }}
    a {{ color: #075e91; }}
    @media (max-width: 760px) {{ .pair, .cards, .qualifications {{ grid-template-columns: 1fr; }} }}
    @media print {{ :root {{ background: white; }} .banner {{ position: static; }} .card {{ box-shadow: none; break-inside: avoid; }} }}
  </style>
</head>
<body>
  <div class="banner">Recorded model evidence — not live inference or an operational recommendation</div>
  <main>
    <header class="mast">
      <div class="eyebrow">Ripple / Lead evidence / incident IN-26-03365</div>
      <h1>From incident message to candidate response</h1>
      <p>Page created {h(capture_date)} HKT from saved files. The messages describe 15 May 2026; the Reader calls were recorded 29 September and the plan call 13 October. This capture aid runs offline.</p>
      <p class="subtle">Recorded Qwen3:8b inference · original text and proposed actions preserved · operator approval and incident validation outstanding</p>
    </header>

    <section class="section" aria-labelledby="reader-title">
      <div class="eyebrow">B · Incident Reader</div>
      <h2 id="reader-title">The closure changed in the feed</h2>
      <p>The first TD report says only “part of the lanes”; the later update says “all lanes.” The Reader saved <code>unspecified</code> and <code>all</code> respectively. These are recorded extractions, not fresh calls.</p>
{messages}
    </section>

    <section class="section" aria-labelledby="plans-title">
      <div class="eyebrow">D · Plan Generator</div>
      <h2 id="plans-title">Three saved candidates, each constraint checked</h2>
      <p>Recorded Qwen3:8b call: {h(bundle['d_call']['timestamp'])}. P0 is the no-intervention reference. P1 and P2 share the only detour in the working context; P2 changes the advised shares and proposes a signal extension. These are proposal parameters, not measured benefits.</p>
      <div class="cards">{plans}</div>
      <div class="qualifications" style="margin-top:1rem">
        <article class="card">
          <h3>Context known retrospectively</h3>
          <p>Action window: {h(context['active_from'])} to {h(context['active_until'])}. The end time is known from the later incident record. The supported detour also draws on TD’s 09:36 update, after the 09:01 first report.</p>
          <p>OD demand comes from the model. Route classifications are working assumptions. School exposure is marked conservatively; the action window misses the stated school peaks.</p>
        </article>
        <article class="card">
          <h3>Review status</h3>
          <p>Data reviewed the v2 context as working assumptions. A constraint pass checks the supplied policy rules. The plan set has not been accepted through an incident replay.</p>
          <p class="caution"><strong>P0 NO-GO:</strong> Data and Simulation have not accepted the incident P0 as a credible basis for ranking these plans. No travel time, delay, queue, emissions or savings claim follows from this page.</p>
        </article>
      </div>
    </section>

    <section class="section" aria-labelledby="trace-title">
      <div class="eyebrow">Traceability</div>
      <h2 id="trace-title">Original files and raw-byte SHA-256</h2>
      <p>Source paths below are repository relative. The page contains the selected evidence so it remains readable by itself offline. Checksums detect changed files; they do not establish scientific validation.</p>
      <div class="source-table"><table><thead><tr><th>Source</th><th>Path</th><th>SHA-256</th></tr></thead><tbody>{source_rows}</tbody></table></div>
      <p class="subtle">The separate <a href="../../docs/lead-genai-follow-up-2026-10-13.md">current Lead status note</a> records F separately. Visuals may capture this page, with the persistent label visible.</p>
    </section>
  </main>
</body>
</html>
"""


def build(root, out, capture_date):
    root = Path(root).resolve()
    out = Path(out).resolve()
    if out.parent != root / "evidence" / "demo" or out.suffix != ".html":
        raise ValueError("Output must be an .html file directly under evidence/demo")
    if capture_date not in out.name:
        raise ValueError("Output filename must contain the page creation date")
    page = render(read_bundle(root), capture_date)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(page)
    return hashlib.sha256(out.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-date", required=True, help="Page creation date, YYYY-MM-DD (HKT)")
    parser.add_argument("--out", required=True, type=Path, help="New HTML path under evidence/demo")
    args = parser.parse_args()
    digest = build(ROOT, args.out, args.capture_date)
    print(f"Wrote {args.out} (SHA-256 {digest}); recorded B/D evidence only.")


if __name__ == "__main__":
    main()
