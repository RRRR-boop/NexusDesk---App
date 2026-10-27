from __future__ import annotations

from nexusdesk.services.diskpilot.volumes_service import classify_free_space


def test_ok_when_well_above_warning_threshold() -> None:
    assert classify_free_space(free_bytes=500, total_bytes=1000) == "ok"


def test_warning_below_warning_threshold() -> None:
    assert classify_free_space(free_bytes=100, total_bytes=1000, warning_percent=15.0) == "warning"


def test_alert_below_alert_threshold() -> None:
    assert classify_free_space(free_bytes=20, total_bytes=1000, alert_percent=5.0) == "alert"


def test_zero_total_bytes_is_ok_rather_than_dividing_by_zero() -> None:
    assert classify_free_space(free_bytes=0, total_bytes=0) == "ok"
