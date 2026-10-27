"""Dépôt des groupes de doublons DiskPilot (section 11)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from nexusdesk.database.session import session_scope
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.diskpilot import DiskDuplicateFile, DiskDuplicateGroup
from nexusdesk.models.diskpilot_domain import DuplicateGroup


class DiskPilotDuplicateRepository:
    def __init__(self, session_factory: sessionmaker[Session], write_queue: WriteQueue) -> None:
        self._session_factory = session_factory
        self._write_queue = write_queue

    def save_duplicate_groups(self, scan_id: int, groups: list[DuplicateGroup]) -> None:
        def _op(session: Session) -> None:
            for group in groups:
                group_row = DiskDuplicateGroup(
                    scan_id=scan_id,
                    size_bytes=group.size_bytes,
                    file_count=len(group.files),
                    recoverable_bytes=group.recoverable_bytes,
                    suggested_keep_path=str(group.suggested_keep),
                )
                session.add(group_row)
                session.flush()
                session.add_all(
                    [
                        DiskDuplicateFile(
                            group_id=group_row.id,
                            path=str(file_node.path),
                            modified_at=file_node.modified_at,
                            is_suggested_keep=(file_node.path == group.suggested_keep),
                        )
                        for file_node in group.files
                    ]
                )

        self._write_queue.submit_write(_op).result()

    def get_duplicate_groups(self, scan_id: int) -> list[DiskDuplicateGroup]:
        with session_scope(self._session_factory) as session:
            rows = (
                session.execute(
                    select(DiskDuplicateGroup).where(DiskDuplicateGroup.scan_id == scan_id)
                )
                .scalars()
                .all()
            )
            session.expunge_all()
            return list(rows)

    def get_duplicate_files(self, group_id: int) -> list[DiskDuplicateFile]:
        with session_scope(self._session_factory) as session:
            rows = (
                session.execute(
                    select(DiskDuplicateFile).where(DiskDuplicateFile.group_id == group_id)
                )
                .scalars()
                .all()
            )
            session.expunge_all()
            return list(rows)
