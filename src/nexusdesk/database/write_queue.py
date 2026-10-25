"""File d'écriture SQLite unique (ADR-0007).

Toute écriture métier doit passer par :meth:`WriteQueue.submit_write` plutôt que d'ouvrir
une transaction directement, afin d'éviter les verrous intermittents entre fils de travail
concurrents. Le thread consommateur est dédié et vit tout le cycle de vie de l'application ;
il n'utilise pas la boucle d'événements Qt, ce qui le rend testable sans ``QApplication``.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from concurrent.futures import Future
from typing import Any, TypeVar

from sqlalchemy.orm import Session, sessionmaker

from nexusdesk.database.session import session_scope

T = TypeVar("T")

_Job = tuple[Callable[[Session], Any], "Future[Any]"]


class WriteQueue:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._queue: queue.Queue[_Job | None] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True, name="nexusdesk-write-queue")
        self._thread.start()

    def submit_write(self, fn: Callable[[Session], T]) -> Future[T]:
        future: Future[T] = Future()
        self._queue.put((fn, future))
        return future

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                break
            fn, future = item
            try:
                with session_scope(self._session_factory) as session:
                    result = fn(session)
            except Exception as exc:
                future.set_exception(exc)
            else:
                future.set_result(result)

    def stop(self, timeout: float = 3.0) -> None:
        """Arrêt propre : draine la file puis attend la fin du thread, borné à ``timeout``."""
        self._queue.put(None)
        self._thread.join(timeout=timeout)
