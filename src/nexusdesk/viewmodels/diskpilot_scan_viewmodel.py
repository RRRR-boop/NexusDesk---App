"""Viewmodel d'un scan DiskPilot : lance le scan en tâche de fond, détient le résultat en
mémoire pour le binding direct au treemap (section 11)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.errors import Cancelled
from nexusdesk.core.tasks import Progress, TaskManager
from nexusdesk.models.diskpilot_domain import ScanOptions, ScanResult, flatten_folder_tree
from nexusdesk.repositories.diskpilot_scan_repository import DiskPilotScanRepository
from nexusdesk.services.diskpilot.export_service import export_files_csv, export_folders_csv
from nexusdesk.services.diskpilot.ports import GetHardlinkKey, GetSizeOnDisk
from nexusdesk.services.diskpilot.scanner import build_scan_task

_TASK_KEY = "diskpilot:scan"


class ScanViewModel(QObject):
    scan_started = Signal(str)
    progress = Signal(Progress)
    scan_finished = Signal(object)
    scan_failed = Signal(str)
    scan_cancelled = Signal()

    def __init__(
        self,
        get_size_on_disk: GetSizeOnDisk,
        get_hardlink_key: GetHardlinkKey,
        scan_repository: DiskPilotScanRepository,
        task_manager: TaskManager,
    ) -> None:
        super().__init__()
        self._get_size_on_disk = get_size_on_disk
        self._get_hardlink_key = get_hardlink_key
        self._scan_repository = scan_repository
        self._task_manager = task_manager
        self.last_result: ScanResult | None = None
        self._last_options: ScanOptions | None = None

    def start_scan(self, root: Path, min_duplicate_size: int = 1_048_576) -> None:
        options = ScanOptions(root=root, min_duplicate_size=min_duplicate_size)
        self._last_options = options
        task = build_scan_task(options, self._get_size_on_disk, self._get_hardlink_key)

        signals = self._task_manager.submit(_TASK_KEY, task)
        if signals is None:
            return
        signals.progress.connect(self.progress.emit)
        signals.finished.connect(self._on_finished)
        signals.failed.connect(self._on_failed)
        self.scan_started.emit(str(root))

    def cancel(self) -> None:
        self._task_manager.cancel(_TASK_KEY)

    def _on_finished(self, result: object) -> None:
        if not isinstance(result, ScanResult):
            return
        options = self._last_options
        if options is None:
            return
        scan_id = self._scan_repository.save_completed_scan(options, result)
        result.scan_id = scan_id
        self.last_result = result
        self.scan_finished.emit(result)

    def _on_failed(self, exc: Exception) -> None:
        if isinstance(exc, Cancelled):
            self.scan_cancelled.emit()
        else:
            self.scan_failed.emit(str(exc))

    def export_files_csv(self, destination: Path) -> None:
        if self.last_result is not None:
            export_files_csv(self.last_result.largest_files, destination)

    def export_folders_csv(self, destination: Path) -> None:
        if self.last_result is not None:
            export_folders_csv(flatten_folder_tree(self.last_result.root), destination)
