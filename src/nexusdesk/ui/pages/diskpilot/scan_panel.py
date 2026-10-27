"""Panneau Scan & Treemap DiskPilot (section 11) : sélection de racine, progression,
avertissements, navigation dans le treemap par double-clic."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nexusdesk.core.tasks import Progress
from nexusdesk.models.diskpilot_domain import FolderNode, ScanResult
from nexusdesk.ui.components.formatting import format_bytes
from nexusdesk.ui.pages.diskpilot.treemap_widget import TreemapWidget
from nexusdesk.ui.theme.tokens import ThemeName, colors_for
from nexusdesk.viewmodels.diskpilot_scan_viewmodel import ScanViewModel


class ScanPanel(QWidget):
    scan_completed = Signal(object)  # ScanResult

    def __init__(
        self,
        viewmodel: ScanViewModel,
        default_min_duplicate_size: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._min_duplicate_size = default_min_duplicate_size
        self._theme: ThemeName = "dark"
        self._breadcrumb: list[FolderNode] = []

        self._root_edit = QLineEdit()
        self._root_edit.setReadOnly(True)
        self._root_edit.setPlaceholderText("Choisissez un dossier à analyser…")

        browse_button = QPushButton("Parcourir…")
        browse_button.clicked.connect(self._on_browse_clicked)

        self._start_button = QPushButton("Démarrer")
        self._start_button.setProperty("role", "primary")
        self._start_button.setEnabled(False)
        self._start_button.clicked.connect(self._on_start_clicked)

        self._cancel_button = QPushButton("Annuler")
        self._cancel_button.setEnabled(False)
        self._cancel_button.clicked.connect(self._viewmodel.cancel)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(self._root_edit, stretch=1)
        selector_layout.addWidget(browse_button)
        selector_layout.addWidget(self._start_button)
        selector_layout.addWidget(self._cancel_button)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._status_label = QLabel("En attente d'un scan.")
        self._status_label.setProperty("role", "caption")

        self._summary_label = QLabel("")
        self._summary_label.setProperty("role", "caption")
        self._summary_label.setWordWrap(True)

        self._breadcrumb_label = QLabel("")
        self._breadcrumb_label.setProperty("role", "caption")
        self._up_button = QPushButton("Remonter")
        self._up_button.setEnabled(False)
        self._up_button.clicked.connect(self._on_up_clicked)

        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.addWidget(self._breadcrumb_label, stretch=1)
        breadcrumb_layout.addWidget(self._up_button)

        self._treemap = TreemapWidget()
        self._treemap.folder_opened.connect(self._on_folder_opened)

        export_files_button = QPushButton("Exporter les fichiers (CSV)")
        export_files_button.clicked.connect(self._on_export_files_clicked)
        export_folders_button = QPushButton("Exporter les dossiers (CSV)")
        export_folders_button.clicked.connect(self._on_export_folders_clicked)
        export_layout = QHBoxLayout()
        export_layout.addStretch(1)
        export_layout.addWidget(export_files_button)
        export_layout.addWidget(export_folders_button)

        layout = QVBoxLayout(self)
        layout.addLayout(selector_layout)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)
        layout.addWidget(self._summary_label)
        layout.addLayout(breadcrumb_layout)
        layout.addWidget(self._treemap, stretch=1)
        layout.addLayout(export_layout)

        viewmodel.scan_started.connect(self._on_scan_started)
        viewmodel.progress.connect(self._on_progress)
        viewmodel.scan_finished.connect(self._on_scan_finished)
        viewmodel.scan_failed.connect(self._on_scan_failed)
        viewmodel.scan_cancelled.connect(self._on_scan_cancelled)

    def set_theme(self, theme: ThemeName) -> None:
        self._theme = theme
        if self._breadcrumb:
            self._treemap.set_folder(self._breadcrumb[-1], colors_for(self._theme))

    def _on_browse_clicked(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choisir un dossier à analyser")
        if directory:
            self._root_edit.setText(directory)
            self._start_button.setEnabled(True)

    def _on_start_clicked(self) -> None:
        root_text = self._root_edit.text()
        if not root_text:
            return
        self._start_button.setEnabled(False)
        self._cancel_button.setEnabled(True)
        self._viewmodel.start_scan(Path(root_text), self._min_duplicate_size)

    def _reset_buttons(self) -> None:
        self._start_button.setEnabled(bool(self._root_edit.text()))
        self._cancel_button.setEnabled(False)

    def _on_scan_started(self, root: str) -> None:
        self._progress_bar.setRange(0, 0)  # indéterminé : le total de fichiers est inconnu
        self._status_label.setText(f"Analyse de {root}…")
        self._summary_label.setText("")

    def _on_progress(self, progress: Progress) -> None:
        self._status_label.setText(f"{progress.step} — {progress.message}")

    def _on_scan_finished(self, result: object) -> None:
        self._reset_buttons()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(100)
        if not isinstance(result, ScanResult):
            return
        self._status_label.setText("Scan terminé.")
        self._summary_label.setText(
            f"{result.file_count} fichiers, {result.dir_count} dossiers — "
            f"{format_bytes(result.total_logical_size)} (logique), "
            f"{format_bytes(result.total_size_on_disk)} (sur disque) — "
            f"{result.excluded_count} exclus, {result.inaccessible_count} inaccessibles, "
            f"{result.onedrive_placeholder_count} OneDrive à la demande, "
            f"{result.hardlink_dedup_count} liens physiques dédupliqués, "
            f"{result.link_count} liens/jonctions."
        )
        self._breadcrumb = [result.root]
        self._update_breadcrumb()
        self._treemap.set_folder(result.root, colors_for(self._theme))
        self.scan_completed.emit(result)

    def _on_scan_failed(self, message: str) -> None:
        self._reset_buttons()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._status_label.setText(f"Échec du scan : {message}")

    def _on_scan_cancelled(self) -> None:
        self._reset_buttons()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._status_label.setText("Scan annulé.")

    def _on_folder_opened(self, folder: object) -> None:
        if not isinstance(folder, FolderNode):
            return
        self._breadcrumb.append(folder)
        self._update_breadcrumb()
        self._treemap.set_folder(folder, colors_for(self._theme))

    def _on_up_clicked(self) -> None:
        if len(self._breadcrumb) <= 1:
            return
        self._breadcrumb.pop()
        self._update_breadcrumb()
        self._treemap.set_folder(self._breadcrumb[-1], colors_for(self._theme))

    def _update_breadcrumb(self) -> None:
        self._breadcrumb_label.setText(str(self._breadcrumb[-1].path) if self._breadcrumb else "")
        self._up_button.setEnabled(len(self._breadcrumb) > 1)

    def _on_export_files_clicked(self) -> None:
        destination, _filter = QFileDialog.getSaveFileName(
            self, "Exporter les fichiers", filter="CSV (*.csv)"
        )
        if destination:
            self._viewmodel.export_files_csv(Path(destination))

    def _on_export_folders_clicked(self) -> None:
        destination, _filter = QFileDialog.getSaveFileName(
            self, "Exporter les dossiers", filter="CSV (*.csv)"
        )
        if destination:
            self._viewmodel.export_folders_csv(Path(destination))
