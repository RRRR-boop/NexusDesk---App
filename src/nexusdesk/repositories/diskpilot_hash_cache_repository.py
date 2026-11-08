"""Dépôt du cache d'empreintes DiskPilot (ADR-0015) : base SQLite séparée, sa propre file
d'écriture — donnée dérivée et jetable, hors de la chaîne Alembic principale.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session, sessionmaker

from nexusdesk.database.session import session_scope
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.diskpilot_cache import FileHashCache


class DiskPilotHashCacheRepository:
    def __init__(self, session_factory: sessionmaker[Session], write_queue: WriteQueue) -> None:
        self._session_factory = session_factory
        self._write_queue = write_queue

    def get(self, path: str, size: int, mtime: float) -> FileHashCache | None:
        """Renvoie la ligne en cache seulement si elle correspond encore exactement à la
        taille et à la date de modification données (sinon le fichier a changé depuis, le
        cache est considéré périmé)."""
        with session_scope(self._session_factory) as session:
            row = session.get(FileHashCache, path)
            if row is None or row.size != size or row.mtime != mtime:
                return None
            session.expunge(row)
            return row

    def upsert(
        self,
        path: str,
        size: int,
        mtime: float,
        kind: Literal["partial", "full"],
        digest: str,
    ) -> None:
        def _op(session: Session) -> None:
            row = session.get(FileHashCache, path)
            if row is None or row.size != size or row.mtime != mtime:
                transient = FileHashCache(
                    path=path,
                    size=size,
                    mtime=mtime,
                    partial_sha256=None,
                    full_sha256=None,
                    last_seen_at=datetime.now(),
                )
                row = session.merge(transient)
            if kind == "partial":
                row.partial_sha256 = digest
            else:
                row.full_sha256 = digest
            row.size = size
            row.mtime = mtime
            row.last_seen_at = datetime.now()

        self._write_queue.submit_write(_op).result()
