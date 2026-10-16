"""Unit checks for D's capacity-bounded share calculation (no simulator)."""
import pytest

from src.plans.capacity_bound import capacity_share_cap


def mock_context():
    return {
        "incident_id": "MOCK-INCIDENT",
        "active_from": "2026-01-01T17:00:00+08:00",
        "active_until": "2026-01-01T18:00:00+08:00",
        "od_demand_vehicles": {"mock_od": 1000},
    }


def mock_rule():
    return {
        "incident_id": "MOCK-INCIDENT",
        "od_group": "mock_od",
        "estimated_spare_veh_h": 200,
        "max_compliance": 0.5,
        "reserve_fraction": 0.2,
        "share_step": 0.01,
    }


def test_capacity_share_cap_uses_window_reserve_and_compliance():
    cap, demand_rate, raw = capacity_share_cap(mock_context(), mock_rule())
    assert demand_rate == 1000
    assert raw == pytest.approx(0.32)
    assert cap == 0.32


def test_capacity_share_cap_rounds_down_and_checks_incident():
    rule = mock_rule()
    rule["estimated_spare_veh_h"] = 207
    assert capacity_share_cap(mock_context(), rule)[0] == 0.33
    rule["incident_id"] = "OTHER"
    with pytest.raises(ValueError, match="another incident"):
        capacity_share_cap(mock_context(), rule)
