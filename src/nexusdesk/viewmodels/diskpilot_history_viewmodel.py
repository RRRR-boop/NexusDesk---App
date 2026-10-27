"""Viewmodel de l'historique des scans et de leur comparaison (section 11)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskManager
from nexusdesk.models.diskpilot_domain import FileNode
from nexusdesk.repositories.diskpilot_scan_repository import DiskPilotScanRepository
from nexusdesk.services.diskpilot.comparison_service import compare_scans

_TASK_KEY = "diskpilot:compare_scans"


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
