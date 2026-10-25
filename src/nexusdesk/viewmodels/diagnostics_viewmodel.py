"""Orchestre l'exécution des contrôles de diagnostic via le gestionnaire de tâches.

Les contrôles concrets sont injectés par la racine de composition (``app.py``) ; ce
viewmodel ne connaît que l'interface abstraite ``core.diagnostics``.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from nexusdesk.core.diagnostics import DiagnosticCheck, DiagnosticResult, run_all
from nexusdesk.core.tasks import CancellationToken, TaskManager

_TASK_KEY = "diagnostics:run_all"


class DiagnosticsViewModel(QObject):
    results_ready = Signal(list)
    failed = Signal(str)

    def __init__(self, checks: list[DiagnosticCheck], task_manager: TaskManager) -> None:
        super().__init__()
        self._checks = checks
        self._task_manager = task_manager

    def run_diagnostics(self) -> None:
        def _task(_token: CancellationToken, _reporter: object) -> list[DiagnosticResult]:
            return run_all(self._checks)

        signals = self._task_manager.submit(_TASK_KEY, _task)
        if signals is None:
            return
        signals.finished.connect(self._on_finished)
        signals.failed.connect(self._on_failed)

    def _on_finished(self, result: object) -> None:
        self.results_ready.emit(result)

    def _on_failed(self, exc: Exception) -> None:
        self.failed.emit(str(exc))
