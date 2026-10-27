"""Panneau Historique DiskPilot (section 11) : 5 derniers scans complets d'une racine,
comparaison entre deux scans sélectionnés (sur l'échantillon des 1000 plus gros fichiers,
seule donnée par fichier conservée au-delà du scan courant)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nexusdesk.models.diskpilot import DiskScan
from nexusdesk.models.diskpilot_domain import ComparisonResult
from nexusdesk.ui.components.formatting import format_bytes
from nexusdesk.viewmodels.diskpilot_history_viewmodel import ScanHistoryViewModel


class HistoryPanel(QWidget):
    def __init__(self, viewmodel: ScanHistoryViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._root: Path | None = None
        self._scans: list[DiskScan] = []

        title = QLabel("Historique")
        title.setProperty("role", "sectionTitle")

        self._refresh_button = QPushButton("Actualiser")
        self._refresh_button.setEnabled(False)
        self._refresh_button.clicked.connect(self._on_refresh_clicked)

        self._compare_button = QPushButton("Comparer les 2 scans sélectionnés")
        self._compare_button.setEnabled(False)
        self._compare_button.clicked.connect(self._on_compare_clicked)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._compare_button)
        header.addWidget(self._refresh_button)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Date", "Fichiers", "Taille logique"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        self._comparison_label = QLabel("")
        self._comparison_label.setProperty("role", "caption")
        self._comparison_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self._table, stretch=1)
        layout.addWidget(self._comparison_label)

        viewmodel.recent_ready.connect(self._on_recent_ready)
        viewmodel.comparison_ready.connect(self._on_comparison_ready)
        viewmodel.failed.connect(self._on_failed)

    def set_root(self, root: Path) -> None:
        self._root = root
        self._refresh_button.setEnabled(True)
        self._viewmodel.load_recent(root)

    def _on_refresh_clicked(self) -> None:
        if self._root is not None:
            self._viewmodel.load_recent(self._root)

    def _on_recent_ready(self, scans: list[DiskScan]) -> None:
        self._scans = scans
        self._table.setRowCount(len(scans))
        for row, scan in enumerate(scans):
            started = scan.started_at.strftime("%Y-%m-%d %H:%M")
            self._table.setItem(row, 0, QTableWidgetItem(started))
            self._table.setItem(row, 1, QTableWidgetItem(str(scan.file_count)))
            self._table.setItem(row, 2, QTableWidgetItem(format_bytes(scan.total_logical_size)))

    def _selected_rows(self) -> list[int]:
        rows = {index.row() for index in self._table.selectedIndexes()}
        return sorted(rows)

    def _on_selection_changed(self) -> None:
        self._compare_button.setEnabled(len(self._selected_rows()) == 2)

    def _on_compare_clicked(self) -> None:
        rows = self._selected_rows()
        if len(rows) != 2:
            return
        first, second = (self._scans[row] for row in rows)
        before, after = (
            (first, second) if first.started_at <= second.started_at else (second, first)
        )
        self._comparison_label.setText("Comparaison en cours…")
        self._viewmodel.compare_scans_by_id(before.id, after.id)

    def _on_comparison_ready(self, result: object) -> None:
        if not isinstance(result, ComparisonResult):
            return
        sign = "+" if result.size_delta >= 0 else "-"
        delta_text = f"{sign}{format_bytes(abs(result.size_delta))}"
        self._comparison_label.setText(
            f"{len(result.added)} fichier(s) apparu(s), {len(result.removed)} disparu(s), "
            f"{len(result.grown)} de taille modifiée — {delta_text} au total (échantillon "
            "des plus gros fichiers de chaque scan)."
        )

    def _on_failed(self, message: str) -> None:
        self._comparison_label.setText(f"Erreur : {message}")
