from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.migration_runner import ensure_up_to_date
from nexusdesk.database.session import make_session_factory
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.diskpilot_domain import (
    DuplicateGroup,
    FileNode,
    FolderNode,
    ScanOptions,
    ScanResult,
)
from nexusdesk.repositories.diskpilot_duplicate_repository import DiskPilotDuplicateRepository
from nexusdesk.repositories.diskpilot_scan_repository import DiskPilotScanRepository

_ROOT = Path(r"C:\root")


def _build_repositories(
    tmp_path: Path,
) -> tuple[DiskPilotDuplicateRepository, DiskPilotScanRepository]:
    db_path = tmp_path / "nexusdesk.db"
    engine = create_sqlite_engine(db_path)
    ensure_up_to_date(engine, db_path, tmp_path / "backups")
    session_factory = make_session_factory(engine)
    write_queue = WriteQueue(session_factory)
    return (
        DiskPilotDuplicateRepository(session_factory, write_queue),
        DiskPilotScanRepository(session_factory, write_queue),
    )


def _insert_bare_scan(scan_repository: DiskPilotScanRepository) -> int:
    folder = FolderNode(path=_ROOT, depth=0)
    result = ScanResult(
        scan_id=0,
        root=folder,
        started_at=datetime(2026, 1, 1),
        finished_at=datetime(2026, 1, 1),
        status="completed",
        file_count=0,
        dir_count=1,
        total_logical_size=0,
        total_size_on_disk=0,
        excluded_count=0,
        inaccessible_count=0,
        onedrive_placeholder_count=0,
        hardlink_dedup_count=0,
        link_count=0,
        largest_files=[],
        skipped=[],
        links=[],
    )
    return scan_repository.save_completed_scan(ScanOptions(root=_ROOT), result)


def test_save_and_get_duplicate_groups_round_trip(tmp_path: Path) -> None:
    duplicate_repository, scan_repository = _build_repositories(tmp_path)
    scan_id = _insert_bare_scan(scan_repository)

    keep = FileNode(
        path=Path(r"C:\root\keep.txt"),
        logical_size=100,
        size_on_disk=100,
        modified_at=datetime(2026, 1, 1),
        category="documents",
    )
    extra = FileNode(
        path=Path(r"C:\root\extra.txt"),
        logical_size=100,
        size_on_disk=100,
        modified_at=datetime(2026, 1, 1),
        category="documents",
    )
    group = DuplicateGroup(
        size_bytes=100, files=[keep, extra], suggested_keep=keep.path, recoverable_bytes=100
    )

    duplicate_repository.save_duplicate_groups(scan_id, [group])

    saved_groups = duplicate_repository.get_duplicate_groups(scan_id)
    assert len(saved_groups) == 1
    assert saved_groups[0].size_bytes == 100
    assert saved_groups[0].file_count == 2

    saved_files = duplicate_repository.get_duplicate_files(saved_groups[0].id)
    paths_and_keep = {f.path: f.is_suggested_keep for f in saved_files}
    assert paths_and_keep[r"C:\root\keep.txt"] is True
    assert paths_and_keep[r"C:\root\extra.txt"] is False
