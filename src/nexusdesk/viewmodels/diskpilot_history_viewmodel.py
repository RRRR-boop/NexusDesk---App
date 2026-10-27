"""Viewmodel de l'historique des scans et de leur comparaison (section 11)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskManager
from nexusdesk.models.diskpilot import DiskLargestFile
from nexusdesk.models.diskpilot_domain import Category, FileNode
from nexusdesk.repositories.diskpilot_scan_repository import DiskPilotScanRepository
from nexusdesk.services.diskpilot.comparison_service import compare_scans

_TASK_KEY = "diskpilot:compare_scans"


def _to_file_node(row: DiskLargestFile) -> FileNode:
    """Reconstruit un ``FileNode`` à partir d'une ligne persistée : seuls les 1000 plus
    gros fichiers sont conservés par scan, donc une comparaison historique ne porte que sur
    cet échantillon plutôt que sur l'arbre complet (jamais ré-analysé depuis le disque)."""
    return FileNode(
        path=Path(row.path),
        logical_size=row.logical_size,
        size_on_disk=row.size_on_disk,
        modified_at=row.modified_at,
        category=cast(Category, row.category),
        is_onedrive_placeholder=row.is_onedrive_placeholder,
    )


class ScanHistoryViewModel(QObject):
    recent_ready = Signal(list)
    comparison_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, scan_repository: DiskPilotScanRepository, task_manager: TaskManager) -> None:
        super().__init__()
        self._scan_repository = scan_repository
        self._task_manager = task_manager

    def load_recent(self, root: Path) -> None:
        scans = self._scan_repository.get_recent_scans(root)
        self.recent_ready.emit(scans)

    def compare(self, before: list[FileNode], after: list[FileNode]) -> None:
        def _task(_token: CancellationToken, _reporter: ProgressReporter) -> object:
            return compare_scans(before, after)

        signals = self._task_manager.submit(_TASK_KEY, _task)
        if signals is None:
            return
        signals.finished.connect(self.comparison_ready.emit)
        signals.failed.connect(lambda exc: self.failed.emit(str(exc)))

    def compare_scans_by_id(self, before_scan_id: int, after_scan_id: int) -> None:
        before_files = [
            _to_file_node(row) for row in self._scan_repository.get_largest_files(before_scan_id)
        ]
        after_files = [
            _to_file_node(row) for row in self._scan_repository.get_largest_files(after_scan_id)
        ]
        self.compare(before_files, after_files)
