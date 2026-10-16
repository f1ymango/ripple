"""The offline Tuen Mun card stays tied to the saved, matched grid."""

from copy import deepcopy
import json

import pytest

from scripts import build_tuen_mun_result_card as card


def test_saved_card_figures_and_visible_qualifications():
    bundle = card.read_bundle()
    assert bundle["p1_vs_p0_pct"] == pytest.approx(37.31)
    assert bundle["p2_vs_p0_pct"] == pytest.approx(-4.31)
    assert bundle["detour_charged_pct"] == pytest.approx(-3.70, abs=0.01)
    assert bundle["p2_lower_cells"] == 17
    page = card.render(bundle)
    assert "SIMULATED CANDIDATE — P0 QUEUE UNDER REVIEW" in page
    assert "+37.3%" in page and "-4.3%" in page and "-3.7%" in page
    assert "Stricter Tuen Mun protocol" in page
    assert "does <strong>not</strong> pass" in page
    assert "Simulation has not accepted it" in page
    assert "No live inference or evaluator run" in page
    for digest in bundle["hashes"].values():
        assert digest in page


def test_card_matches_shipped_capture():
    expected = card.render(card.read_bundle())
    assert card.DEFAULT_OUT.read_text(encoding="utf-8") == expected


def test_changed_ranking_or_mixed_comparison_is_rejected():
    documents = {
        label: json.loads((card.ROOT / path).read_text(encoding="utf-8"))
        for label, path in card.SOURCES.items() if path.endswith(".json")
    }
    altered = deepcopy(documents)
    altered["Team ranking"]["first"] = None
    with pytest.raises(ValueError, match="ranking changed"):
        card.validate_bundle(altered, {})

    altered = deepcopy(documents)
    altered["Detour-inclusive comparison"][0]["plans"]["P2"]["delay_E"] += 1
    with pytest.raises(ValueError, match="E delay differs"):
        card.validate_bundle(altered, {})


def test_frozen_share_change_is_rejected():
    documents = {
        label: json.loads((card.ROOT / path).read_text(encoding="utf-8"))
        for label, path in card.SOURCES.items() if path.endswith(".json")
    }
    documents["P2 plan"]["diversions"][0]["share"] = 0.2
    with pytest.raises(ValueError, match="advice changed"):
        card.validate_bundle(documents, {})
