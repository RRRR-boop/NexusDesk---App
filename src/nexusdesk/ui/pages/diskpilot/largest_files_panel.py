"""Panneau Plus gros fichiers DiskPilot (section 11) : classement des 1000 plus gros
fichiers du dernier scan, suppression sélective vers la Corbeille."""

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

from nexusdesk.models.diskpilot_domain import FileNode, ScanResult
from nexusdesk.services.diskpilot.ports import RevealInExplorer
from nexusdesk.ui.components.formatting import format_bytes
from nexusdesk.ui.pages.diskpilot.deletion_dialog import DeletionDialog
from nexusdesk.viewmodels.diskpilot_deletion_viewmodel import DeletionViewModel

_CATEGORY_LABELS = {
    "videos": "Vidéos",
    "images": "Images",
    "audio": "Audio",
    "documents": "Documents",
    "archives": "Archives",
    "installers": "Installateurs",
    "code": "Code",
    "other": "Autre",
}


class LargestFilesPanel(QWidget):
    def __init__(
        self,
        deletion_viewmodel: DeletionViewModel,
        reveal_in_explorer: RevealInExplorer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._deletion_viewmodel = deletion_viewmodel
        self._reveal_in_explorer = reveal_in_explorer
        self._files: list[FileNode] = []
        self._scan_root: Path | None = None

        title = QLabel("Plus gros fichiers")
        title.setProperty("role", "sectionTitle")

        self._reveal_button = QPushButton("Afficher dans l'Explorateur")
        self._reveal_button.setEnabled(False)
        self._reveal_button.clicked.connect(self._on_reveal_clicked)

        self._delete_button = QPushButton("Supprimer la sélection")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._on_delete_clicked)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._reveal_button)
        header.addWidget(self._delete_button)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Chemin", "Taille", "Catégorie", "Modifié le"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self._table, stretch=1)

    def set_result(self, result: ScanResult) -> None:
        self._scan_root = result.root.path
        self._files = result.largest_files
        self._refresh_table()

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
            self._reveal_in_explorer(self._files[rows[0]].path)

    def _on_delete_clicked(self) -> None:
        rows = self._selected_rows()
        if not rows or self._scan_root is None:
            return
        selected_nodes = [self._files[row] for row in rows]
        paths = [node.path for node in selected_nodes]
        sizes = {node.path: node.logical_size for node in selected_nodes}
        mtimes = {node.path: node.modified_at.timestamp() for node in selected_nodes}

        dialog = DeletionDialog(
            self._deletion_viewmodel, paths, sizes, mtimes, self._scan_root, parent=self
        )
        dialog.exec()
        if dialog.result_report is not None and dialog.result_report.succeeded:
            succeeded = set(dialog.result_report.succeeded)
            self._files = [node for node in self._files if node.path not in succeeded]
            self._refresh_table()

    def _refresh_table(self) -> None:
        self._table.setRowCount(len(self._files))
        for row, node in enumerate(self._files):
            self._table.setItem(row, 0, QTableWidgetItem(str(node.path)))
            self._table.setItem(row, 1, QTableWidgetItem(format_bytes(node.logical_size)))
            self._table.setItem(
                row, 2, QTableWidgetItem(_CATEGORY_LABELS.get(node.category, node.category))
            )
            self._table.setItem(
                row, 3, QTableWidgetItem(node.modified_at.strftime("%Y-%m-%d %H:%M"))
            )
