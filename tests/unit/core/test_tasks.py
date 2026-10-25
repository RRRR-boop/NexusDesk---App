from __future__ import annotations

import time
from typing import Any

from nexusdesk.core.errors import Cancelled
from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskManager


def test_submit_deduplicates_by_key(qtbot: Any) -> None:
    manager = TaskManager()
    started: list[int] = []

    def _task(_token: CancellationToken, _reporter: ProgressReporter) -> str:
        started.append(1)
        time.sleep(0.3)
        return "done"

    signals_1 = manager.submit("same-key", _task)
    signals_2 = manager.submit("same-key", _task)

    assert signals_1 is not None
    assert signals_2 is None  # déduplication : une tâche identique tourne déjà

    with qtbot.waitSignal(signals_1.finished, timeout=2000):
        pass

    assert len(started) == 1


def test_cancellation_token_respected(qtbot: Any) -> None:
    manager = TaskManager()

    def _task(token: CancellationToken, _reporter: ProgressReporter) -> int:
        count = 0
        while not token.is_cancelled and count < 1000:
            count += 1
            time.sleep(0.01)
        token.raise_if_cancelled()
        return count

    signals = manager.submit("cancellable", _task)
    assert signals is not None

    failures: list[Exception] = []
    signals.failed.connect(failures.append)

    time.sleep(0.05)
    manager.cancel("cancellable")

    with qtbot.waitSignal(signals.failed, timeout=2000):
        pass

    assert len(failures) == 1
    assert isinstance(failures[0], Cancelled)


def test_progress_rate_is_bounded(qtbot: Any) -> None:
    manager = TaskManager()
    emitted: list[float] = []

    def _task(_token: CancellationToken, reporter: ProgressReporter) -> None:
        for i in range(200):
            reporter.report(i / 200, "etape")
        reporter.report(1.0, "fin")

    signals = manager.submit("progress-test", _task)
    assert signals is not None
    signals.progress.connect(lambda _progress: emitted.append(time.monotonic()))

    with qtbot.waitSignal(signals.finished, timeout=2000):
        pass

    # Débit borné à ~10/s (section 4) : pour une tâche qui tente 200 émissions quasi
    # instantanées, on attend beaucoup moins de 200 signaux réellement publiés.
    assert len(emitted) < 50


def test_unexpected_exception_is_captured_not_raised(qtbot: Any) -> None:
    manager = TaskManager()

    def _task(_token: CancellationToken, _reporter: ProgressReporter) -> None:
        raise ValueError("boom")

    signals = manager.submit("error-test", _task)
    assert signals is not None

    failures: list[Exception] = []
    signals.failed.connect(failures.append)

    with qtbot.waitSignal(signals.failed, timeout=2000):
        pass

    assert len(failures) == 1
    assert isinstance(failures[0], ValueError)
