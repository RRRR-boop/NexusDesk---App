"""Jauge colorée réutilisable (volumes, espace libre...) — section 5 : jamais de couleur
codée en dur, tout vient de ``ui/theme/tokens.py``."""

from __future__ import annotations

from PySide6.QtWidgets import QProgressBar, QWidget

from nexusdesk.ui.theme.tokens import ColorTokens

_STATUS_COLOR_ATTR = {
    "ok": "status_success",
    "warning": "status_warning",
    "alert": "status_danger",
}


class GaugeBar(QProgressBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTextVisible(False)
        self.setRange(0, 100)

    def set_value_and_status(self, percent: float, status: str, colors: ColorTokens) -> None:
        self.setValue(round(percent))
        color_attr = _STATUS_COLOR_ATTR.get(status, "status_success")
        color = getattr(colors, color_attr)
        self.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
            f"QProgressBar {{ background-color: {colors.bg_raised}; border-radius: 4px; }}"
        )
