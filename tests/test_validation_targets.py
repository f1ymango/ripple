"""The one validation rule E, F and the console share (src/validation_targets.py)."""
import pytest

from src import validation_targets as targets

V1 = {"geh_under_5_pct": 88.0, "speed_mape_pct": 11.3}
V2 = {"geh_under_5_pct": 93.52, "speed_mape_pct": 24.83, "speed_mape_free_flow_pct": 12.99,
      "congestion_state_agreement_pct": 93.27, "wrong_lane_teleports_not_at_lane_shut": 0}


def test_a_version_1_block_keeps_the_earlier_rule():
    assert targets.check(V1) == (True, "")
    assert not targets.met({**V1, "speed_mape_pct": 24.83})          # whole-run speed error still decides version 1
    assert not targets.is_version_2(V1)


def test_a_version_2_block_is_judged_on_free_flow_speed_and_congestion_state():
    assert targets.check(V2) == (True, "")                           # whole-run 24.83% is information only
    assert targets.is_version_2(V2)


@pytest.mark.parametrize("change, reason", [
    ({"geh_under_5_pct": 84.99}, "GEH"),
    ({"speed_mape_free_flow_pct": 15.01}, "free-flow speed"),
    ({"congestion_state_agreement_pct": 84.99}, "congestion-state"),
    ({"wrong_lane_teleports_not_at_lane_shut": 1}, "wrong-lane teleport"),
])
def test_each_version_2_target_on_its_own_fails_the_baseline(change, reason):
    met, why = targets.check({**V2, **change})
    assert not met and reason in why


@pytest.mark.parametrize("validation", [None, {}, {"geh_under_5_pct": 90}, {**V2, "speed_mape_free_flow_pct": "12"},
                                        {**V2, "congestion_state_agreement_pct": 101}, {**V1, "geh_under_5_pct": -1},
                                        {**V2, "speed_mape_free_flow_pct": float("nan")}, {**V1, "speed_mape_pct": True}])
def test_a_missing_or_malformed_block_never_passes(validation):
    assert not targets.met(validation)
