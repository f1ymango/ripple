from datetime import datetime

from src.twin import audit_lane_scope


def test_optional_raw_lane_readings_preserve_feed_values_and_coverage(tmp_path, monkeypatch):
    stamp = "20260515-0901"
    (tmp_path / f"{stamp}.xml").write_bytes(b"<snapshot />")
    monkeypatch.setattr(audit_lane_scope.archive, "read_cached", lambda *_: b"<snapshot />")
    monkeypatch.setattr(
        audit_lane_scope.detectors,
        "parse_snapshot",
        lambda *_args, **_kwargs: [
            {"timestamp": datetime.fromisoformat("2026-05-15T09:00:00+08:00"),
             "detector_id": "AID01104", "lane": "Fast Lane", "volume": 7,
             "speed_kmh": 19.0, "occupancy_pct": 2.0, "valid": True, "period_s": 30.0},
            {"timestamp": datetime.fromisoformat("2026-05-15T09:00:00+08:00"),
             "detector_id": "AID01104", "lane": "Slow Lane", "volume": 0,
             "speed_kmh": None, "occupancy_pct": 0.0, "valid": True, "period_s": 30.0},
        ],
    )

    report = audit_lane_scope.build_report(
        tmp_path, [stamp], ["AID01104"], include_lane_readings=True)

    lanes = report["detectors"]["AID01104"]["lane_readings"][0]["lanes"]
    assert lanes == [
        {"lane_id": "Fast Lane", "raw_volume": 7, "speed_kmh": 19.0,
         "occupancy_pct": 2.0, "valid": True, "period_seconds": 30.0},
        {"lane_id": "Slow Lane", "raw_volume": 0, "speed_kmh": None,
         "occupancy_pct": 0.0, "valid": True, "period_seconds": 30.0},
    ]
    assert "lane_readings" not in audit_lane_scope.build_report(tmp_path, [stamp], ["AID01104"])[
        "detectors"]["AID01104"]
