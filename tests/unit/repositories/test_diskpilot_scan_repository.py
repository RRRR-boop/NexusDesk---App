"""Rétention des scans DiskPilot (ADR-0013) : 5 derniers scans ``completed`` conservés par
racine, suppression en cascade des tables enfants pour les scans purgés."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.migration_runner import ensure_up_to_date
from nexusdesk.database.session import make_session_factory, session_scope
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.diskpilot import DiskFolderSnapshot, DiskLargestFile, DiskScan
from nexusdesk.models.diskpilot_domain import FileNode, FolderNode, ScanOptions, ScanResult
from nexusdesk.repositories.diskpilot_scan_repository import DiskPilotScanRepository

_ROOT = Path(r"C:\Users\test\Documents")


def _build_repository(tmp_path: Path) -> tuple[DiskPilotScanRepository, object]:
    db_path = tmp_path / "nexusdesk.db"
    engine = create_sqlite_engine(db_path)
    ensure_up_to_date(engine, db_path, tmp_path / "backups")
    session_factory = make_session_factory(engine)
    write_queue = WriteQueue(session_factory)
    return DiskPilotScanRepository(session_factory, write_queue), session_factory


def _build_result(started_at: datetime, status: str = "completed") -> ScanResult:
    file_node = FileNode(
        path=_ROOT / "fichier.txt",
        logical_size=100,
        size_on_disk=100,
        modified_at=started_at,
        category="documents",
    )
    folder = FolderNode(path=_ROOT, depth=0, files=[file_node], logical_size=100, file_count=1)
    return ScanResult(
        scan_id=0,
        root=folder,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=1),
        status=status,  # type: ignore[arg-type]
        file_count=1,
        dir_count=1,
        total_logical_size=100,
        total_size_on_disk=100,
        excluded_count=0,
        inaccessible_count=0,
        onedrive_placeholder_count=0,
        hardlink_dedup_count=0,
        link_count=0,
        largest_files=[file_node],
        skipped=[],
        links=[],
    )


def test_only_five_most_recent_completed_scans_are_kept(tmp_path: Path) -> None:
    repository, session_factory = _build_repository(tmp_path)
    options = ScanOptions(root=_ROOT)
    base = datetime(2026, 1, 1)

    scan_ids = [
        repository.save_completed_scan(options, _build_result(base + timedelta(days=i)))
        for i in range(7)
    ]

    remaining_ids = {scan.id for scan in repository.get_recent_scans(_ROOT, limit=100)}
    assert len(remaining_ids) == 5
    # Les deux plus anciens (index 0 et 1) doivent avoir ete purges.
    assert scan_ids[0] not in remaining_ids
    assert scan_ids[1] not in remaining_ids
    assert scan_ids[6] in remaining_ids


def test_purged_scan_children_are_cascade_deleted(tmp_path: Path) -> None:
    repository, session_factory = _build_repository(tmp_path)
    options = ScanOptions(root=_ROOT)
    base = datetime(2026, 1, 1)

    scan_ids = [
        repository.save_completed_scan(options, _build_result(base + timedelta(days=i)))
        for i in range(7)
    ]
    purged_id = scan_ids[0]

    with session_scope(session_factory) as session:  # type: ignore[arg-type]
        folders = (
            session.execute(
                select(DiskFolderSnapshot).where(DiskFolderSnapshot.scan_id == purged_id)
            )
            .scalars()
            .all()
        )
        files = (
            session.execute(select(DiskLargestFile).where(DiskLargestFile.scan_id == purged_id))
            .scalars()
            .all()
        )
        scan_row = session.get(DiskScan, purged_id)

    assert folders == []
    assert files == []
    assert scan_row is None


def test_cancelled_scan_for_same_root_is_removed_on_next_scan(tmp_path: Path) -> None:
    repository, session_factory = _build_repository(tmp_path)
    options = ScanOptions(root=_ROOT)

    cancelled_result = _build_result(datetime(2026, 1, 1), status="cancelled")
    cancelled_id = repository.save_completed_scan(options, cancelled_result)

    repository.save_completed_scan(options, _build_result(datetime(2026, 1, 2)))

    with session_scope(session_factory) as session:  # type: ignore[arg-type]
        assert session.get(DiskScan, cancelled_id) is None


def test_mark_stale_running_as_failed_heals_orphaned_scan(tmp_path: Path) -> None:
    repository, session_factory = _build_repository(tmp_path)

    with session_scope(session_factory) as session:  # type: ignore[arg-type]
        row = DiskScan(
            root_path=str(_ROOT),
            normalized_root_path=str(_ROOT).lower(),
            started_at=datetime(2026, 1, 1),
            finished_at=None,
            status="running",
        )
        session.add(row)
        session.flush()
        running_id = row.id

    repository.mark_stale_running_as_failed()

    with session_scope(session_factory) as session:  # type: ignore[arg-type]
        healed = session.get(DiskScan, running_id)
        assert healed is not None
        assert healed.status == "failed"
