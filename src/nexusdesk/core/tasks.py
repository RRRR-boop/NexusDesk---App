"""Gestionnaire de tâches unique encapsulant ``QThreadPool`` (section 4).

Toute opération de plus de 100 ms doit passer par ici plutôt que de bloquer le fil
principal. Chaque tâche a une clé de déduplication, un jeton d'annulation, une progression
publiée par signal Qt (débit borné) et un résultat ou une erreur typée.

Point d'attention : une exception levée dans ``QRunnable.run()`` ne remonte jamais au fil
principal ni à ``sys.excepthook`` — elle est silencieusement perdue. ``_Runnable`` capture
donc systématiquement toute exception et l'émet via le signal ``failed``.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from nexusdesk.core.errors import Cancelled, NexusDeskError

_logger = logging.getLogger("nexusdesk.tasks")

_MIN_PROGRESS_INTERVAL_SECONDS = 0.1  # borne le débit à ~10 mises à jour/seconde


@dataclass(frozen=True)
class Progress:
    fraction: float
    step: str
    message: str = ""


class CancellationToken:
    """Jeton d'annulation coopératif : la tâche doit vérifier ``is_cancelled`` dans ses boucles."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise Cancelled("Tâche annulée par l'utilisateur.")


class WorkerSignals(QObject):
    progress = Signal(Progress)
    finished = Signal(object)
    failed = Signal(Exception)


TaskFn = Callable[[CancellationToken, "ProgressReporter"], object]


class ProgressReporter:
    """Passée à chaque tâche pour publier sa progression sans dépasser le débit autorisé."""

    def __init__(self, signals: WorkerSignals) -> None:
        self._signals = signals
        self._last_emit = 0.0
        self._last_step: str | None = None

    def report(self, fraction: float, step: str, message: str = "") -> None:
        now = time.monotonic()
        should_emit = (
            fraction >= 1.0
            or step != self._last_step
            or (now - self._last_emit) >= _MIN_PROGRESS_INTERVAL_SECONDS
        )
        if not should_emit:
            return
        self._last_emit = now
        self._last_step = step
        self._signals.progress.emit(Progress(fraction=fraction, step=step, message=message))


class _Runnable(QRunnable):
    def __init__(self, fn: TaskFn, token: CancellationToken, signals: WorkerSignals) -> None:
        super().__init__()
        self._fn = fn
        self._token = token
        self._signals = signals

    def run(self) -> None:
        reporter = ProgressReporter(self._signals)
        try:
            result = self._fn(self._token, reporter)
        except NexusDeskError as exc:
            self._signals.failed.emit(exc)
        except Exception as exc:  # noqa: BLE001 - doit être capturée ici, jamais s'échapper
            _logger.exception("Erreur non typée dans une tâche de fond.")
            self._signals.failed.emit(exc)
        else:
            self._signals.finished.emit(result)


class TaskManager(QObject):
    """Déduplique les tâches par clé et les soumet à un ``QThreadPool`` dédié."""

    def __init__(self, max_thread_count: int | None = None) -> None:
        super().__init__()
        self._pool = QThreadPool()
        if max_thread_count is not None:
            self._pool.setMaxThreadCount(max_thread_count)
        self._running: dict[str, tuple[CancellationToken, WorkerSignals]] = {}

    def is_running(self, key: str) -> bool:
        return key in self._running

    def submit(self, key: str, fn: TaskFn) -> WorkerSignals | None:
        """Soumet une tâche ; renvoie ``None`` si une tâche identique tourne déjà."""
        if key in self._running:
            _logger.debug("Tâche '%s' déjà en cours, soumission ignorée.", key)
            return None

        token = CancellationToken()
        signals = WorkerSignals()
        self._running[key] = (token, signals)

        def _cleanup(_result: Any) -> None:
            self._running.pop(key, None)

        def _cleanup_on_error(_exc: Exception) -> None:
            self._running.pop(key, None)

        signals.finished.connect(_cleanup)
        signals.failed.connect(_cleanup_on_error)

        runnable = _Runnable(fn, token, signals)
        self._pool.start(runnable)
        return signals

    def cancel(self, key: str) -> None:
        entry = self._running.get(key)
        if entry is not None:
            entry[0].cancel()

    def cancel_all(self) -> None:
        for token, _signals in self._running.values():
            token.cancel()

    def wait_for_done(self, timeout_ms: int = 3000) -> bool:
        return self._pool.waitForDone(timeout_ms)
