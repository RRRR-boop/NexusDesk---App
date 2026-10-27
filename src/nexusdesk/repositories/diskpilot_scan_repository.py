"""Dépôt des scans DiskPilot (section 11) : écriture par lots, rétention (5 derniers scans
``completed`` par dossier racine, cf. ADR-0013), auto-guérison des scans orphelins.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from nexusdesk.database.session import session_scope
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.diskpilot import (
    DiskFolderSnapshot,
    DiskLargestFile,
    DiskLinkEntry,
    DiskScan,
    DiskSkippedEntry,
)
from nexusdesk.models.diskpilot_domain import (
    Category,
    ScanOptions,
    ScanResult,
    flatten_folder_tree,
)

_MAX_PERSISTED_DEPTH = 4
_BATCH_SIZE = 500
_SCANS_TO_KEEP = 5


def _batched[T](items: list[T], size: int) -> Iterator[list[T]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _normalize_root(root: Path) -> str:
    return str(root.resolve()).lower()


def _dump_category_sizes(sizes: dict[Category, int]) -> str:
    return json.dumps(sizes)


class DiskPilotScanRepository:
    def __init__(self, session_factory: sessionmaker[Session], write_queue: WriteQueue) -> None:
        self._session_factory = session_factory
        self._write_queue = write_queue

    def mark_stale_running_as_failed(self) -> None:
        """Auto-guérison au démarrage : une ligne ``running`` orpheline après un crash
        de l'application devient ``failed`` plutôt que de rester indéfiniment active."""

        def _op(session: Session) -> None:
            stale = (
                session.execute(select(DiskScan).where(DiskScan.status == "running"))
                .scalars()
                .all()
            )
            for scan in stale:
                scan.status = "failed"
                scan.error_message = "Interrompu par un arrêt inattendu de l'application."
                scan.finished_at = datetime.now()

        self._write_queue.submit_write(_op).result()

    def save_completed_scan(self, options: ScanOptions, result: ScanResult) -> int:
        """Écrit un scan terminé (scan, dossiers ≤4 niveaux, 1000 plus gros fichiers,
        entrées ignorées, liens) et applique la rétention. Renvoie l'id du scan créé."""

        def _op(session: Session) -> int:
            normalized_root = _normalize_root(options.root)
            scan_row = DiskScan(
                root_path=str(options.root),
                normalized_root_path=normalized_root,
                started_at=result.started_at,
                finished_at=result.finished_at,
                status=result.status,
                file_count=result.file_count,
                dir_count=result.dir_count,
                total_logical_size=result.total_logical_size,
                total_size_on_disk=result.total_size_on_disk,
                excluded_count=result.excluded_count,
                inaccessible_count=result.inaccessible_count,
                onedrive_placeholder_count=result.onedrive_placeholder_count,
                hardlink_dedup_count=result.hardlink_dedup_count,
                link_count=result.link_count,
                options_json=json.dumps({"min_duplicate_size": options.min_duplicate_size}),
                error_message=None,
            )
            session.add(scan_row)
            session.flush()
            scan_id = scan_row.id

            persisted_folders = [
                folder
                for folder in flatten_folder_tree(result.root)
                if folder.depth <= _MAX_PERSISTED_DEPTH
            ]
            for batch in _batched(persisted_folders, _BATCH_SIZE):
                session.add_all(
                    [
                        DiskFolderSnapshot(
                            scan_id=scan_id,
                            path=str(folder.path),
                            parent_path=(str(folder.path.parent) if folder.depth > 0 else None),
                            depth=folder.depth,
                            logical_size=folder.logical_size,
                            size_on_disk=folder.size_on_disk,
                            file_count=folder.file_count,
                            category_sizes_json=_dump_category_sizes(folder.category_sizes),
                        )
                        for folder in batch
                    ]
                )

            ranked_files = list(enumerate(result.largest_files, start=1))
            for file_batch in _batched(ranked_files, _BATCH_SIZE):
                session.add_all(
                    [
                        DiskLargestFile(
                            scan_id=scan_id,
                            path=str(node.path),
                            logical_size=node.logical_size,
                            size_on_disk=node.size_on_disk,
                            modified_at=node.modified_at,
                            category=node.category,
                            is_onedrive_placeholder=node.is_onedrive_placeholder,
                            rank=rank,
                        )
                        for rank, node in file_batch
                    ]
                )

            for skipped_batch in _batched(result.skipped, _BATCH_SIZE):
                session.add_all(
                    [
                        DiskSkippedEntry(
                            scan_id=scan_id,
                            path=str(entry.path),
                            kind=entry.kind,
                            reason=entry.reason,
                        )
                        for entry in skipped_batch
                    ]
                )

            for link_batch in _batched(result.links, _BATCH_SIZE):
                session.add_all(
                    [
                        DiskLinkEntry(
                            scan_id=scan_id,
                            path=str(entry.path),
                            link_type=entry.link_type,
                            target_path=str(entry.target_path) if entry.target_path else None,
                            is_broken=entry.is_broken,
                        )
                        for entry in link_batch
                    ]
                )

            session.flush()
            self._prune_locked(session, normalized_root, scan_id)
            return scan_id

        return self._write_queue.submit_write(_op).result()

    @staticmethod
    def _prune_locked(session: Session, normalized_root: str, current_scan_id: int) -> None:
        """Rétention : 5 derniers scans ``completed`` par racine ; les scans
        ``cancelled``/``failed`` précédents pour cette racine n'ont pas vocation à
        persister au-delà du scan suivant."""
        keep_ids = (
            select(DiskScan.id)
            .where(
                DiskScan.normalized_root_path == normalized_root,
                DiskScan.status == "completed",
            )
            .order_by(DiskScan.started_at.desc())
            .limit(_SCANS_TO_KEEP)
        )
        session.execute(
            delete(DiskScan).where(
                DiskScan.normalized_root_path == normalized_root,
                DiskScan.status == "completed",
                DiskScan.id.not_in(keep_ids),
            )
        )
        session.execute(
            delete(DiskScan).where(
                DiskScan.normalized_root_path == normalized_root,
                DiskScan.status.in_(("cancelled", "failed")),
                DiskScan.id != current_scan_id,
            )
        )

    def prune_old_scans(self, root: Path, keep: int = _SCANS_TO_KEEP) -> None:
        """Rétention appelable indépendamment (tests, maintenance) sans nouveau scan."""
        normalized_root = _normalize_root(root)

        def _op(session: Session) -> None:
            keep_ids = (
                select(DiskScan.id)
                .where(
                    DiskScan.normalized_root_path == normalized_root,
                    DiskScan.status == "completed",
                )
                .order_by(DiskScan.started_at.desc())
                .limit(keep)
            )
            session.execute(
                delete(DiskScan).where(
                    DiskScan.normalized_root_path == normalized_root,
                    DiskScan.status == "completed",
                    DiskScan.id.not_in(keep_ids),
                )
            )

        self._write_queue.submit_write(_op).result()

    def get_recent_scans(self, root: Path, limit: int = _SCANS_TO_KEEP) -> list[DiskScan]:
        normalized_root = _normalize_root(root)
        with session_scope(self._session_factory) as session:
            rows = (
                session.execute(
                    select(DiskScan)
                    .where(
                        DiskScan.normalized_root_path == normalized_root,
                        DiskScan.status == "completed",
                    )
                    .order_by(DiskScan.started_at.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            session.expunge_all()
            return list(rows)

    def get_scan(self, scan_id: int) -> DiskScan | None:
        with session_scope(self._session_factory) as session:
            row = session.get(DiskScan, scan_id)
            if row is not None:
                session.expunge(row)
            return row

    def get_largest_files(self, scan_id: int) -> list[DiskLargestFile]:
        with session_scope(self._session_factory) as session:
            rows = (
                session.execute(
                    select(DiskLargestFile)
                    .where(DiskLargestFile.scan_id == scan_id)
                    .order_by(DiskLargestFile.rank)
                )
                .scalars()
                .all()
            )
            session.expunge_all()
            return list(rows)

    def get_folder_snapshots(self, scan_id: int) -> list[DiskFolderSnapshot]:
        with session_scope(self._session_factory) as session:
            rows = (
                session.execute(
                    select(DiskFolderSnapshot).where(DiskFolderSnapshot.scan_id == scan_id)
                )
                .scalars()
                .all()
            )
            session.expunge_all()
            return list(rows)

    def count_scans_for_root(self, root: Path) -> int:
        normalized_root = _normalize_root(root)
        with session_scope(self._session_factory) as session:
            return len(
                session.execute(
                    select(DiskScan.id).where(
                        DiskScan.normalized_root_path == normalized_root,
                        DiskScan.status == "completed",
                    )
                )
                .scalars()
                .all()
            )
