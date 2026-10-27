"""Classification des jauges de volume (section 11) : fonction pure."""

from __future__ import annotations

from typing import Literal

GaugeStatus = Literal["ok", "warning", "alert"]

DEFAULT_WARNING_PERCENT = 15.0
DEFAULT_ALERT_PERCENT = 5.0


def classify_free_space(
    free_bytes: int,
    total_bytes: int,
    warning_percent: float = DEFAULT_WARNING_PERCENT,
    alert_percent: float = DEFAULT_ALERT_PERCENT,
) -> GaugeStatus:
    if total_bytes <= 0:
        return "ok"
    free_percent = (free_bytes / total_bytes) * 100
    if free_percent < alert_percent:
        return "alert"
    if free_percent < warning_percent:
        return "warning"
    return "ok"
