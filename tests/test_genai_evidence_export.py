"""Checks for the recorded B/D page; synthetic changes stay in memory or tmp."""

from copy import deepcopy
import json

import pytest

from scripts import build_genai_evidence as evidence


def mock_bundle_root(tmp_path):
    root = tmp_path / "mock_bundle"
    for relative in evidence.SOURCES.values():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((evidence.ROOT / relative).read_bytes())
    return root


def test_selected_records_and_saved_candidates_match_original_calls():
    bundle = evidence.read_bundle()
    assert [item["id"] for item in bundle["messages"]] == ["138270", "138272"]
    assert [item["parsed"]["incident"]["lanes_closed"]
            for item in bundle["messages"]] == [["unspecified"], ["all"]]
    assert [plan["plan_id"] for plan in bundle["plans"]] == ["P0", "P1", "P2"]
    assert bundle["hashes"]["P2 candidate"] == evidence.EXPECTED_PLAN_HASHES["P2 candidate"]


def test_tampered_candidate_hash_is_rejected(tmp_path):
    root = mock_bundle_root(tmp_path)
    candidate = root / evidence.SOURCES["P2 candidate"]
    candidate.write_bytes(candidate.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="P2 candidate changed"):
        evidence.read_bundle(root)


def test_tampered_reader_extraction_is_rejected(tmp_path):
    root = mock_bundle_root(tmp_path)
    saved = root / evidence.SOURCES["Saved Reader output"]
    rows = evidence.read_jsonl(saved.read_bytes())
    first = evidence.exact_one(rows, lambda row: row.get("message_id") == "138270",
                               "mock Reader output")
    first["incident"]["notes"] = "mock tampered note"
    saved.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
                     encoding="utf-8")
    with pytest.raises(ValueError, match="Saved Reader output 138270 differs"):
        evidence.read_bundle(root)


@pytest.mark.parametrize("rows,expected", [([], "found 0"),
                                           ([{"id": 1}, {"id": 1}], "found 2")])
def test_missing_or_duplicate_record_is_rejected(rows, expected):
    with pytest.raises(ValueError, match=expected):
        evidence.exact_one(rows, lambda row: row["id"] == 1, "mock record")


def test_html_escapes_source_text_and_keeps_all_limitations():
    bundle = deepcopy(evidence.read_bundle())
    bundle["messages"][0]["raw"]["stn"]["CONTENT_EN"] = '<script src="https://bad.example/x.js">oops</script>'
    bundle["messages"][0]["parsed"]["incident"]["notes"] = '<img src=x onerror=alert(1)>'
    page = evidence.render(bundle, "2026-10-13")
    assert "&lt;script src=&quot;https://bad.example/x.js&quot;&gt;" in page
    assert "&lt;img src=x onerror=alert(1)&gt;" in page
    assert "<script" not in page and "<img" not in page
    assert "<link" not in page and "@import" not in page and "url(" not in page
    assert 'href="https://' not in page and 'src="https://' not in page
    for label in ("Recorded model evidence", "P0 NO-GO", "retrospectively",
                  "proposal parameters", "Original title says", "working assumptions"):
        assert label in page


def test_existing_output_is_preserved(tmp_path, monkeypatch):
    root = tmp_path / "mock_bundle"
    out = root / "evidence" / "demo" / "mock_recorded-2026-10-13.html"
    out.parent.mkdir(parents=True)
    out.write_text("keep this earlier capture", encoding="utf-8")
    original_read_bundle = evidence.read_bundle
    monkeypatch.setattr(evidence, "read_bundle", lambda _root: original_read_bundle(evidence.ROOT))
    with pytest.raises(FileExistsError):
        evidence.build(root, out, "2026-10-13")
    assert out.read_text(encoding="utf-8") == "keep this earlier capture"


def test_output_is_scoped_to_demo_directory(tmp_path):
    with pytest.raises(ValueError, match="evidence/demo"):
        evidence.build(tmp_path, tmp_path / "mock_escape-2026-10-13.html", "2026-10-13")
