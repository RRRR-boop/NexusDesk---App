"""Panneau Nettoyage DiskPilot (section 11) : suggestions présentées comme des pistes à
vérifier, jamais comme des fichiers « inutiles » affirmés avec certitude."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nexusdesk.models.diskpilot_domain import CleanupSuggestion, FileNode
from nexusdesk.services.diskpilot.ports import RevealInExplorer
from nexusdesk.ui.components.formatting import format_bytes
from nexusdesk.ui.pages.diskpilot.deletion_dialog import DeletionDialog
from nexusdesk.viewmodels.diskpilot_cleanup_viewmodel import CleanupSuggestionsViewModel
from nexusdesk.viewmodels.diskpilot_deletion_viewmodel import DeletionViewModel
from nexusdesk.viewmodels.diskpilot_duplicates_viewmodel import DuplicatesViewModel

_KIND_LABELS = {
    "old_installer": "Installateur ancien",
    "temp_file": "Fichier temporaire",
    "duplicate": "Doublon",
    "stale_large_file": "Gros fichier ancien",
}


class CleanupPanel(QWidget):
    def __init__(
        self,
        viewmodel: CleanupSuggestionsViewModel,
        duplicates_viewmodel: DuplicatesViewModel,
        deletion_viewmodel: DeletionViewModel,
        reveal_in_explorer: RevealInExplorer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._duplicates_viewmodel = duplicates_viewmodel
        self._deletion_viewmodel = deletion_viewmodel
        self._reveal_in_explorer = reveal_in_explorer
        self._files: list[FileNode] = []
        self._scan_root: Path | None = None
        self._suggestions: list[CleanupSuggestion] = []

        title = QLabel("Nettoyage")
        title.setProperty("role", "sectionTitle")

        self._refresh_button = QPushButton("Rafraîchir les suggestions")
        self._refresh_button.setEnabled(False)
        self._refresh_button.clicked.connect(self._on_refresh_clicked)

        self._storage_sense_button = QPushButton("Ouvrir l'Assistant Stockage")
        self._storage_sense_button.clicked.connect(self._viewmodel.open_storage_sense)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._storage_sense_button)
        header.addWidget(self._refresh_button)

        self._reveal_button = QPushButton("Afficher dans l'Explorateur")
        self._reveal_button.setEnabled(False)
        self._reveal_button.clicked.connect(self._on_reveal_clicked)

        self._delete_button = QPushButton("Supprimer la sélection")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._on_delete_clicked)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch(1)
        actions_layout.addWidget(self._reveal_button)
        actions_layout.addWidget(self._delete_button)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Type", "Chemin", "Taille", "Détail"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addLayout(actions_layout)
        layout.addWidget(self._table, stretch=1)

        viewmodel.suggestions_ready.connect(self._on_suggestions_ready)
        viewmodel.storage_sense_unavailable.connect(self._on_storage_sense_unavailable)

    def set_scan_data(self, files: list[FileNode], scan_root: Path) -> None:
        self._files = files
        self._scan_root = scan_root
        self._refresh_button.setEnabled(True)

    def _on_refresh_clicked(self) -> None:
        self._refresh_button.setEnabled(False)
        self._viewmodel.refresh(self._files, self._duplicates_viewmodel.last_groups)

    def _on_suggestions_ready(self, suggestions: list[CleanupSuggestion]) -> None:
        self._refresh_button.setEnabled(True)
        self._suggestions = suggestions
        self._table.setRowCount(len(suggestions))
        for row, suggestion in enumerate(suggestions):
            self._table.setItem(
                row, 0, QTableWidgetItem(_KIND_LABELS.get(suggestion.kind, suggestion.kind))
            )
            self._table.setItem(row, 1, QTableWidgetItem(str(suggestion.path)))
            self._table.setItem(row, 2, QTableWidgetItem(format_bytes(suggestion.size_bytes)))
            self._table.setItem(row, 3, QTableWidgetItem(suggestion.detail))

    def _on_storage_sense_unavailable(self) -> None:
        QMessageBox.warning(
            self,
            "Assistant Stockage",
            "Impossible d'ouvrir l'Assistant Stockage de Windows.",
        )

    def _selected_rows(self) -> list[int]:
        rows = {index.row() for index in self._table.selectedIndexes()}
        return sorted(rows)

    def _on_selection_changed(self) -> None:
        rows = self._selected_rows()
        self._delete_button.setEnabled(bool(rows))
        self._reveal_button.setEnabled(len(rows) == 1)

    def _on_reveal_clicked(self) -> None:
        rows = self._selected_rows()
        if len(rows) == 1:
            self._reveal_in_explorer(self._suggestions[rows[0]].path)

    def _on_delete_clicked(self) -> None:
        rows = self._selected_rows()
        if not rows or self._scan_root is None:
            return
        selected = [self._suggestions[row] for row in rows]
        paths = [suggestion.path for suggestion in selected]
        sizes = {suggestion.path: suggestion.size_bytes for suggestion in selected}

        dialog = DeletionDialog(
            self._deletion_viewmodel, paths, sizes, {}, self._scan_root, parent=self
        )
        dialog.exec()
        if dialog.result_report is not None and dialog.result_report.succeeded:
            succeeded = set(dialog.result_report.succeeded)
            self._suggestions = [s for s in self._suggestions if s.path not in succeeded]
            self._on_suggestions_ready(self._suggestions)
