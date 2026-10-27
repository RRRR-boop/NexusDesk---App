"""Panneau Volumes DiskPilot (section 11) : une jauge par volume, colorée selon les seuils
réglables (ok/avertissement/alerte)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from nexusdesk.services.diskpilot.ports import VolumeInfoLike
from nexusdesk.services.diskpilot.volumes_service import GaugeStatus
from nexusdesk.ui.components.formatting import format_bytes
from nexusdesk.ui.components.gauge_bar import GaugeBar
from nexusdesk.ui.theme.tokens import SPACING, ThemeName, colors_for
from nexusdesk.viewmodels.diskpilot_volumes_viewmodel import VolumesViewModel

_VOLUME_TYPE_LABELS = {
    "fixed": "disque fixe",
    "removable": "amovible",
    "network": "réseau",
    "optical": "optique",
    "unknown": "inconnu",
}


class VolumesPanel(QWidget):
    def __init__(self, viewmodel: VolumesViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._theme: ThemeName = "dark"

        title = QLabel("Volumes")
        title.setProperty("role", "sectionTitle")

        self._refresh_button = QPushButton("Rafraîchir")
        self._refresh_button.clicked.connect(self._viewmodel.refresh)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._refresh_button)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(SPACING.sm)

        self._empty_label = QLabel("Aucun volume détecté.")
        self._empty_label.setProperty("role", "caption")
        self._rows_layout.addWidget(self._empty_label)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addLayout(self._rows_layout)
        layout.addStretch(1)

        viewmodel.volumes_ready.connect(self._on_volumes_ready)
        viewmodel.failed.connect(self._on_failed)

    def set_theme(self, theme: ThemeName) -> None:
        self._theme = theme

    def refresh(self) -> None:
        self._viewmodel.refresh()

    def _clear_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _on_volumes_ready(self, volumes: list[tuple[VolumeInfoLike, GaugeStatus]]) -> None:
        self._clear_rows()
        if not volumes:
            self._rows_layout.addWidget(self._empty_label)
            return

        colors = colors_for(self._theme)
        for volume, status in volumes:
            row = QWidget()
            row_layout = QVBoxLayout(row)

            name_label = QLabel(f"{volume.letter}  {volume.label}".strip())
            name_label.setProperty("role", "subtitle")

            gauge = GaugeBar()
            percent_used = (
                (volume.used_bytes / volume.total_bytes * 100) if volume.total_bytes > 0 else 0.0
            )
            gauge.set_value_and_status(percent_used, status, colors)

            volume_type_label = _VOLUME_TYPE_LABELS.get(volume.volume_type, volume.volume_type)
            detail = QLabel(
                f"{format_bytes(volume.free_bytes)} libres sur "
                f"{format_bytes(volume.total_bytes)} — {volume.filesystem} ({volume_type_label})"
            )
            detail.setProperty("role", "caption")

            row_layout.addWidget(name_label)
            row_layout.addWidget(gauge)
            row_layout.addWidget(detail)
            self._rows_layout.addWidget(row)

    def _on_failed(self, message: str) -> None:
        self._clear_rows()
        error_label = QLabel(message)
        error_label.setProperty("role", "caption")
        error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._rows_layout.addWidget(error_label)
