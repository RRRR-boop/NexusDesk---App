"""Viewmodel de suppression DiskPilot (section 11) : revérification puis Corbeille."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskManager
from nexusdesk.services.diskpilot.deletion_service import build_preview, execute_deletion
from nexusdesk.services.diskpilot.ports import SendToRecycleBin

_PREVIEW_TASK_KEY = "diskpilot:deletion_preview"
_DELETE_TASK_KEY = "diskpilot:deletion_execute"


class DeletionViewModel(QObject):
    preview_ready = Signal(object)
    deletion_finished = Signal(object)
    failed = Signal(str)

    def __init__(self, send_to_recycle_bin: SendToRecycleBin, task_manager: TaskManager) -> None:
        super().__init__()
        self._send_to_recycle_bin = send_to_recycle_bin
        self._task_manager = task_manager

    def request_preview(
        self,
        paths: list[Path],
        expected_sizes: dict[Path, int],
        expected_mtimes: dict[Path, float],
    ) -> None:
        def _task(_token: CancellationToken, _reporter: ProgressReporter) -> object:
            return build_preview(paths, expected_sizes, expected_mtimes)

        signals = self._task_manager.submit(_PREVIEW_TASK_KEY, _task)
        if signals is None:
            return
        signals.finished.connect(self.preview_ready.emit)
        signals.failed.connect(lambda exc: self.failed.emit(str(exc)))

    def confirm(self, paths: list[Path], sizes: dict[Path, int], scan_root: Path) -> None:
        def _task(_token: CancellationToken, _reporter: ProgressReporter) -> object:
            return execute_deletion(paths, sizes, scan_root, self._send_to_recycle_bin)

        signals = self._task_manager.submit(_DELETE_TASK_KEY, _task)
        if signals is None:
            return
        signals.finished.connect(self.deletion_finished.emit)
        signals.failed.connect(lambda exc: self.failed.emit(str(exc)))
