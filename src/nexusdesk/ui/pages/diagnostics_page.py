"""Page Diagnostic d'installation (section 15) : contrôles enregistrés, exportables plus tard."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nexusdesk.core.diagnostics import DiagnosticResult
from nexusdesk.viewmodels.diagnostics_viewmodel import DiagnosticsViewModel

_STATUS_LABELS = {"ok": "OK", "warning": "Attention", "error": "Erreur", "info": "Info"}


class DiagnosticsPage(QWidget):
    def __init__(self, viewmodel: DiagnosticsViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel

        title = QLabel("Diagnostic d'installation")
        title.setProperty("role", "pageTitle")

        self._run_button = QPushButton("Lancer le diagnostic")
        self._run_button.setProperty("role", "primary")
        self._run_button.clicked.connect(self._on_run_clicked)

        header_layout = QHBoxLayout()
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(self._run_button)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Contrôle", "Statut", "Détail"])
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addWidget(self._table, stretch=1)

        viewmodel.results_ready.connect(self._on_results_ready)
        viewmodel.failed.connect(self._on_failed)

    def _on_run_clicked(self) -> None:
        self._run_button.setEnabled(False)
        self._viewmodel.run_diagnostics()

    def _on_results_ready(self, results: list[DiagnosticResult]) -> None:
        self._run_button.setEnabled(True)
        self._table.setRowCount(len(results))
        for row, result in enumerate(results):
            self._table.setItem(row, 0, QTableWidgetItem(result.name))
            status_label = _STATUS_LABELS.get(result.status, result.status)
            self._table.setItem(row, 1, QTableWidgetItem(status_label))
            self._table.setItem(row, 2, QTableWidgetItem(result.detail))

    def _on_failed(self, message: str) -> None:
        self._run_button.setEnabled(True)
        self._table.setRowCount(1)
        self._table.setItem(0, 0, QTableWidgetItem("Diagnostic"))
        self._table.setItem(0, 1, QTableWidgetItem("Erreur"))
        self._table.setItem(0, 2, QTableWidgetItem(message))
