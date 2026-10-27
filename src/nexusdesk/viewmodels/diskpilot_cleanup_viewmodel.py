"""Viewmodel des suggestions de nettoyage DiskPilot (section 11)."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskManager
from nexusdesk.models.diskpilot_domain import DuplicateGroup, FileNode
from nexusdesk.services.diskpilot.cleanup_suggestions import (
    suggest_from_duplicates,
    suggest_old_installers,
    suggest_stale_large_files,
    suggest_temp_files,
)
from nexusdesk.services.diskpilot.ports import OpenStorageSense

_TASK_KEY = "diskpilot:cleanup_suggestions"


class CleanupSuggestionsViewModel(QObject):
    suggestions_ready = Signal(list)
    storage_sense_unavailable = Signal()

    def __init__(self, open_storage_sense: OpenStorageSense, task_manager: TaskManager) -> None:
        super().__init__()
        self._open_storage_sense = open_storage_sense
        self._task_manager = task_manager

    def refresh(self, files: list[FileNode], duplicate_groups: list[DuplicateGroup]) -> None:
        def _task(_token: CancellationToken, _reporter: ProgressReporter) -> object:
            suggestions = []
            suggestions.extend(suggest_old_installers(files))
            suggestions.extend(suggest_temp_files(files))
            suggestions.extend(suggest_stale_large_files(files))
            suggestions.extend(suggest_from_duplicates(duplicate_groups))
            return suggestions

        signals = self._task_manager.submit(_TASK_KEY, _task)
        if signals is None:
            return
        signals.finished.connect(self.suggestions_ready.emit)

    def open_storage_sense(self) -> None:
        if not self._open_storage_sense():
            self.storage_sense_unavailable.emit()
