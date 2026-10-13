"""Model-free checks for Lead's bounded P2 diagnostic plan sets."""
import json
from pathlib import Path
from shutil import copyfile

import pytest

from src.evaluator.actions import PlanActions
from src.evaluator.run import load_plan
from src.generation import load_json
from src.plans.diagnostic import SOURCE_FILES, VARIANTS, digest, prepare
from src.plans.generator import validate_plans

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/generated-plans/IN-26-03365-lead-draft-20261013-b"
SCENARIO = ROOT / "sim/scenarios/evaluator_IN-26-03365_replay.json"


def test_prepared_variants_preserve_comparators_and_change_only_declared_actions(tmp_path):
    out = tmp_path / "plans"
    source_hashes = {name: digest(SOURCE / name) for name in SOURCE_FILES}
    manifest = prepare(SOURCE, out)
    assert set(manifest["variants"]) == set(VARIANTS)
    assert manifest["source_plan_set"] == SOURCE.relative_to(ROOT).as_posix()
    assert manifest["source_sha256"] == source_hashes
    assert {name: digest(SOURCE / name) for name in SOURCE_FILES} == source_hashes
    assert load_json(out / "manifest.json") == manifest
    original_p2 = load_json(SOURCE / "P2.json")
    scenario = load_json(SCENARIO)

    for plan_set in VARIANTS:
        folder = out / plan_set
        for name in ("P0.json", "P1.json", "generation-inputs.json"):
            assert (folder / name).read_bytes() == (SOURCE / name).read_bytes()
        inputs = load_json(folder / "generation-inputs.json")
        plans = [load_json(folder / f"{plan_id}.json") for plan_id in ("P0", "P1", "P2")]
        assert validate_plans({"plans": plans}, inputs["policy_context"], inputs["incident"]) == plans
        p2 = plans[2]
        assert p2["signals"] == []
        assert p2["vms"] == original_p2["vms"]
        assert p2["priority_corridor"] == original_p2["priority_corridor"]
        assert [(d["od_group"], d["via"]) for d in p2["diversions"]] == [
            (d["od_group"], d["via"]) for d in original_p2["diversions"]]
        assert manifest["variants"][plan_set]["p2_sha256"] == digest(folder / "P2.json")
        actions = PlanActions(p2, inputs["policy_context"], scenario, 0.5, 66)
        assert actions.signals == []
        assert actions.start >= 0
        assert [a["probability"] for a in actions.advice] == [d["share"] * 0.5 for d in p2["diversions"]]
        assert load_plan(folder, "P2", scenario)[0] == p2

    assert [d["share"] for d in load_json(out / "lead-p2-nosignal-oct13/P2.json")["diversions"]] == [0.8, 0.7]
    assert [d["share"] for d in load_json(out / "lead-p2-half-nosignal-oct13/P2.json")["diversions"]] == [0.4, 0.35]


def test_existing_output_is_never_overwritten(tmp_path):
    out = tmp_path / "plans"
    prepare(SOURCE, out)
    before = (out / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError, match="new output directory"):
        prepare(SOURCE, out)
    assert (out / "manifest.json").read_bytes() == before


def test_changed_source_proposal_requires_new_review(tmp_path):
    source = tmp_path / "changed-source"
    source.mkdir()
    for name in SOURCE_FILES:
        copyfile(SOURCE / name, source / name)
    p2 = load_json(source / "P2.json")
    p2["diversions"][0]["share"] = 0.9
    (source / "P2.json").write_text(json.dumps(p2), encoding="utf-8")
    with pytest.raises(ValueError, match="Source plan set bytes changed"):
        prepare(source, tmp_path / "output")
    assert not (tmp_path / "output").exists()
