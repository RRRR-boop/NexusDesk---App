"""Viewmodel de la détection de doublons DiskPilot (section 11)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskManager
from nexusdesk.models.diskpilot_domain import DuplicateGroup, FileNode
from nexusdesk.repositories.diskpilot_duplicate_repository import (
    DiskPilotDuplicateRepository,
)
from nexusdesk.repositories.diskpilot_hash_cache_repository import (
    DiskPilotHashCacheRepository,
)
from nexusdesk.services.diskpilot.duplicate_finder import find_duplicates
from nexusdesk.services.diskpilot.export_service import export_duplicates_csv

_TASK_KEY = "diskpilot:duplicates"


class DuplicatesViewModel(QObject):
    groups_ready = Signal(list)
    failed = Signal(str)

    def __init__(
        self,
        hash_cache_repository: DiskPilotHashCacheRepository,
        duplicate_repository: DiskPilotDuplicateRepository,
        task_manager: TaskManager,
    ) -> None:
        super().__init__()
        self._hash_cache_repository = hash_cache_repository
        self._duplicate_repository = duplicate_repository
        self._task_manager = task_manager
        self.last_groups: list[DuplicateGroup] = []
        self._scan_id: int | None = None

    def find_duplicates(
        self, files: list[FileNode], min_size: int, scan_id: int | None = None
    ) -> None:
        self._scan_id = scan_id

        def _task(token: CancellationToken, _reporter: ProgressReporter) -> object:
            return find_duplicates(files, min_size, self._hash_cache_repository, token)

        signals = self._task_manager.submit(_TASK_KEY, _task)
        if signals is None:
            return
        signals.finished.connect(self._on_finished)
        signals.failed.connect(lambda exc: self.failed.emit(str(exc)))

    def _on_finished(self, result: object) -> None:
        groups = result if isinstance(result, list) else []
        self.last_groups = groups
        if self._scan_id is not None:
            self._duplicate_repository.save_duplicate_groups(self._scan_id, groups)
        self.groups_ready.emit(groups)

    def export_csv(self, destination: Path) -> None:
        if self.last_groups:
            export_duplicates_csv(self.last_groups, destination)
