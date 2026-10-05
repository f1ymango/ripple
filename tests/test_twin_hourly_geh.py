"""Check the hourly-equivalent method and fail on unmatched source bins."""
import json
from pathlib import Path

import pytest

from src.twin.audit_hourly_geh import by_detector, score


def test_hourly_equivalent_scales_missing_bins_and_preserves_zero():
    data = json.loads((Path(__file__).parent / "fixtures" / "mock_hourly_geh.json").read_text(encoding="utf-8"))
    original, upgraded = (score(by_detector(data[k])) for k in ("reference", "candidate"))
    assert original["detectors_under_5"] == 2
    assert upgraded["detectors_under_5"] == 1
    assert upgraded["by_detector"]["A"]["eligible_bins"] == 2
    assert upgraded["by_detector"]["A"]["observed_hourly_equivalent"] == 120
    assert upgraded["by_detector"]["A"]["simulated_hourly_equivalent"] == 240
    assert upgraded["by_detector"]["A"]["geh_on_eligible_bin_sums"] < 5
    assert upgraded["by_detector"]["A"]["geh_hourly_equivalent"] > 5
    assert upgraded["by_detector"]["B"]["geh_hourly_equivalent"] == 0


def test_duplicate_and_negative_counts_fail():
    data = json.loads((Path(__file__).parent / "fixtures" / "mock_hourly_geh.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="Duplicate"):
        by_detector(data["reference"] + data["reference"][:1])
    data["reference"][0]["simulated"] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        by_detector(data["reference"])
