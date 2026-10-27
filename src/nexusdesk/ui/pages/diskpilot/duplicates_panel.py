"""Panneau Doublons DiskPilot (section 11) : recherche par empreinte, sélection rapide des
exemplaires superflus (hors celui suggéré à conserver), suppression vers la Corbeille."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nexusdesk.models.diskpilot_domain import DuplicateGroup, FileNode
from nexusdesk.services.diskpilot.ports import RevealInExplorer
from nexusdesk.ui.components.formatting import format_bytes
from nexusdesk.ui.pages.diskpilot.deletion_dialog import DeletionDialog
from nexusdesk.viewmodels.diskpilot_deletion_viewmodel import DeletionViewModel
from nexusdesk.viewmodels.diskpilot_duplicates_viewmodel import DuplicatesViewModel


class DuplicatesPanel(QWidget):
    def __init__(
        self,
        viewmodel: DuplicatesViewModel,
        deletion_viewmodel: DeletionViewModel,
        reveal_in_explorer: RevealInExplorer,
        default_min_duplicate_size: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._deletion_viewmodel = deletion_viewmodel
        self._reveal_in_explorer = reveal_in_explorer
        self._min_duplicate_size = default_min_duplicate_size
        self._files: list[FileNode] = []
        self._scan_id: int | None = None
        self._scan_root: Path | None = None
        self._rows: list[tuple[FileNode, bool]] = []
        self._group_index_by_row: list[int] = []

        title = QLabel("Doublons")
        title.setProperty("role", "sectionTitle")

        self._search_button = QPushButton("Rechercher les doublons")
        self._search_button.setEnabled(False)
        self._search_button.clicked.connect(self._on_search_clicked)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._search_button)

        self._summary_label = QLabel("Lancez d'abord un scan pour rechercher des doublons.")
        self._summary_label.setProperty("role", "caption")

        self._select_duplicates_button = QPushButton("Sélectionner les doublons (hors conservés)")
        self._select_duplicates_button.setEnabled(False)
        self._select_duplicates_button.clicked.connect(self._on_select_duplicates_clicked)

        self._reveal_button = QPushButton("Afficher dans l'Explorateur")
        self._reveal_button.setEnabled(False)
        self._reveal_button.clicked.connect(self._on_reveal_clicked)

        self._delete_button = QPushButton("Supprimer la sélection")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._on_delete_clicked)

        self._export_button = QPushButton("Exporter (CSV)")
        self._export_button.setEnabled(False)
        self._export_button.clicked.connect(self._on_export_clicked)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self._select_duplicates_button)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self._reveal_button)
        actions_layout.addWidget(self._delete_button)
        actions_layout.addWidget(self._export_button)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Groupe", "Chemin", "Taille", "À conserver"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self._summary_label)
        layout.addLayout(actions_layout)
        layout.addWidget(self._table, stretch=1)

        viewmodel.groups_ready.connect(self._on_groups_ready)
        viewmodel.failed.connect(self._on_failed)

    def set_scan_data(self, files: list[FileNode], scan_id: int | None, scan_root: Path) -> None:
        self._files = files
        self._scan_id = scan_id
        self._scan_root = scan_root
        self._search_button.setEnabled(True)
        self._summary_label.setText("Prêt à rechercher les doublons.")

    def _on_search_clicked(self) -> None:
        self._search_button.setEnabled(False)
        self._summary_label.setText("Recherche de doublons en cours…")
        self._viewmodel.find_duplicates(self._files, self._min_duplicate_size, self._scan_id)

    def _on_groups_ready(self, groups: list[DuplicateGroup]) -> None:
        self._search_button.setEnabled(True)
        recoverable = sum(group.recoverable_bytes for group in groups)
        self._summary_label.setText(
            f"{len(groups)} groupe(s) de doublons — {format_bytes(recoverable)} récupérable(s)."
        )
        self._rows = [
            (file_node, file_node.path == group.suggested_keep)
            for group_index, group in enumerate(groups)
            for file_node in group.files
        ]
        self._group_index_by_row = [
            group_index for group_index, group in enumerate(groups) for _file_node in group.files
        ]
        self._export_button.setEnabled(bool(groups))
        self._refresh_table()

    def _on_failed(self, message: str) -> None:
        self._search_button.setEnabled(True)
        self._summary_label.setText(f"Erreur : {message}")

    def _refresh_table(self) -> None:
        self._table.setRowCount(len(self._rows))
        for row, (file_node, is_keep) in enumerate(self._rows):
            self._table.setItem(row, 0, QTableWidgetItem(str(self._group_index_by_row[row] + 1)))
            self._table.setItem(row, 1, QTableWidgetItem(str(file_node.path)))
            self._table.setItem(row, 2, QTableWidgetItem(format_bytes(file_node.logical_size)))
            self._table.setItem(row, 3, QTableWidgetItem("Oui" if is_keep else ""))

    def _selected_rows(self) -> list[int]:
        rows = {index.row() for index in self._table.selectedIndexes()}
        return sorted(rows)

    def _on_selection_changed(self) -> None:
        rows = self._selected_rows()
        self._delete_button.setEnabled(bool(rows))
        self._reveal_button.setEnabled(len(rows) == 1)

    def _on_select_duplicates_clicked(self) -> None:
        self._table.clearSelection()
        for row, (_file_node, is_keep) in enumerate(self._rows):
            if not is_keep:
                self._table.selectRow(row)

    def _on_reveal_clicked(self) -> None:
        rows = self._selected_rows()
        if len(rows) == 1:
            self._reveal_in_explorer(self._rows[rows[0]][0].path)

    def _on_delete_clicked(self) -> None:
        rows = self._selected_rows()
        if not rows or self._scan_root is None:
            return
        selected_nodes = [self._rows[row][0] for row in rows]
        paths = [node.path for node in selected_nodes]
        sizes = {node.path: node.logical_size for node in selected_nodes}
        mtimes = {node.path: node.modified_at.timestamp() for node in selected_nodes}

        dialog = DeletionDialog(
            self._deletion_viewmodel, paths, sizes, mtimes, self._scan_root, parent=self
        )
        dialog.exec()
        if dialog.result_report is not None and dialog.result_report.succeeded:
            succeeded = set(dialog.result_report.succeeded)
            kept_rows = [
                (group_index, row)
                for group_index, row in zip(self._group_index_by_row, self._rows, strict=True)
                if row[0].path not in succeeded
            ]
            self._group_index_by_row = [group_index for group_index, _row in kept_rows]
            self._rows = [row for _group_index, row in kept_rows]
            self._refresh_table()

    def _on_export_clicked(self) -> None:
        destination, _filter = QFileDialog.getSaveFileName(
            self, "Exporter les doublons", filter="CSV (*.csv)"
        )
        if destination:
            self._viewmodel.export_csv(Path(destination))
