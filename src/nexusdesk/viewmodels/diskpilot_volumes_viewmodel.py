"""Viewmodel des volumes DiskPilot (section 11)."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskManager
from nexusdesk.repositories.settings_repository import SettingsRepository
from nexusdesk.services.diskpilot.ports import ListVolumes
from nexusdesk.services.diskpilot.volumes_service import GaugeStatus, classify_free_space

_TASK_KEY = "diskpilot:list_volumes"


class VolumesViewModel(QObject):
    volumes_ready = Signal(list)
    failed = Signal(str)

    def __init__(
        self,
        list_volumes: ListVolumes,
        settings_repository: SettingsRepository,
        task_manager: TaskManager,
    ) -> None:
        super().__init__()
        self._list_volumes = list_volumes
        self._settings_repository = settings_repository
        self._task_manager = task_manager

    def refresh(self) -> None:
        def _task(_token: CancellationToken, _reporter: ProgressReporter) -> object:
            return list(self._list_volumes())

        signals = self._task_manager.submit(_TASK_KEY, _task)
        if signals is None:
            return
        signals.finished.connect(self._on_finished)
        signals.failed.connect(lambda exc: self.failed.emit(str(exc)))

    def _on_finished(self, result: object) -> None:
        volumes = result if isinstance(result, list) else []
        settings = self._settings_repository.get_all().diskpilot
        enriched: list[tuple[object, GaugeStatus]] = [
            (
                volume,
                classify_free_space(
                    volume.free_bytes,
                    volume.total_bytes,
                    settings.warning_free_percent,
                    settings.alert_free_percent,
                ),
            )
            for volume in volumes
        ]
        self.volumes_ready.emit(enriched)
