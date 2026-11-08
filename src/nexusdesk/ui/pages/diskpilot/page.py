"""Page DiskPilot (section 11) : onglets Volumes / Scan et treemap / Plus gros fichiers /
Doublons / Nettoyage / Historique, assemblés autour du conteneur de viewmodels unique."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from nexusdesk.config.schema import DiskPilotSettings
from nexusdesk.models.diskpilot_domain import FileNode, ScanResult, flatten_folder_tree
from nexusdesk.services.diskpilot.ports import RevealInExplorer
from nexusdesk.ui.pages.diskpilot.cleanup_panel import CleanupPanel
from nexusdesk.ui.pages.diskpilot.duplicates_panel import DuplicatesPanel
from nexusdesk.ui.pages.diskpilot.history_panel import HistoryPanel
from nexusdesk.ui.pages.diskpilot.largest_files_panel import LargestFilesPanel
from nexusdesk.ui.pages.diskpilot.scan_panel import ScanPanel
from nexusdesk.ui.pages.diskpilot.volumes_panel import VolumesPanel
from nexusdesk.ui.theme.tokens import ThemeName
from nexusdesk.viewmodels.diskpilot_viewmodel import DiskPilotViewModel


class DiskPilotPage(QWidget):
    def __init__(
        self,
        viewmodel: DiskPilotViewModel,
        reveal_in_explorer: RevealInExplorer,
        settings: DiskPilotSettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._free_space_thresholds = (settings.warning_free_percent, settings.alert_free_percent)
        default_min_duplicate_size = settings.min_duplicate_size_bytes
        extra_excluded_paths = tuple(Path(path) for path in settings.extra_excluded_paths)

        self._volumes_panel = VolumesPanel(viewmodel.volumes)
        self._scan_panel = ScanPanel(viewmodel.scan, default_min_duplicate_size)
        self._scan_panel.set_extra_excluded_paths(extra_excluded_paths)
        self._largest_files_panel = LargestFilesPanel(viewmodel.deletion, reveal_in_explorer)
        self._duplicates_panel = DuplicatesPanel(
            viewmodel.duplicates,
            viewmodel.deletion,
            reveal_in_explorer,
            default_min_duplicate_size,
        )
        self._cleanup_panel = CleanupPanel(
            viewmodel.cleanup, viewmodel.duplicates, viewmodel.deletion, reveal_in_explorer
        )
        self._history_panel = HistoryPanel(viewmodel.history)

        tabs = QTabWidget()
        tabs.addTab(self._volumes_panel, "Volumes")
        tabs.addTab(self._scan_panel, "Scan et treemap")
        tabs.addTab(self._largest_files_panel, "Plus gros fichiers")
        tabs.addTab(self._duplicates_panel, "Doublons")
        tabs.addTab(self._cleanup_panel, "Nettoyage")
        tabs.addTab(self._history_panel, "Historique")

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)

        self._scan_panel.scan_completed.connect(self._on_scan_completed)
        self._volumes_panel.refresh()

    def set_theme(self, theme: str) -> None:
        resolved: ThemeName = "light" if theme == "light" else "dark"
        self._volumes_panel.set_theme(resolved)
        self._scan_panel.set_theme(resolved)

    def apply_settings(self, settings: DiskPilotSettings) -> None:
        """Applique les réglages DiskPilot sans redémarrage (section 15)."""
        self._scan_panel.set_min_duplicate_size(settings.min_duplicate_size_bytes)
        self._scan_panel.set_extra_excluded_paths(
            tuple(Path(path) for path in settings.extra_excluded_paths)
        )
        self._duplicates_panel.set_min_duplicate_size(settings.min_duplicate_size_bytes)
        thresholds = (settings.warning_free_percent, settings.alert_free_percent)
        if thresholds != self._free_space_thresholds:
            # Les jauges relisent les seuils au rafraîchissement : ne relister les volumes
            # que si les seuils ont réellement changé.
            self._free_space_thresholds = thresholds
            self._volumes_panel.refresh()

    def _on_scan_completed(self, result: object) -> None:
        if not isinstance(result, ScanResult):
            return
        all_files: list[FileNode] = [
            file_node for folder in flatten_folder_tree(result.root) for file_node in folder.files
        ]
        scan_root = result.root.path
        self._largest_files_panel.set_result(result)
        self._duplicates_panel.set_scan_data(all_files, result.scan_id, scan_root)
        self._cleanup_panel.set_scan_data(all_files, scan_root)
        self._history_panel.set_root(scan_root)
