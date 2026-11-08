from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from nexusdesk.models.diskpilot_domain import DuplicateGroup, FileNode
from nexusdesk.services.diskpilot.cleanup_suggestions import (
    suggest_from_duplicates,
    suggest_old_installers,
    suggest_stale_large_files,
    suggest_temp_files,
)

_NOW = datetime(2026, 10, 27, 12, 0, 0)


def _node(path: str, category: str, size: int, days_old: int) -> FileNode:
    return FileNode(
        path=Path(path),
        logical_size=size,
        size_on_disk=size,
        modified_at=_NOW - timedelta(days=days_old),
        category=category,  # type: ignore[arg-type]
    )


def test_old_installer_in_downloads_is_suggested() -> None:
    node = _node(r"C:\Users\x\Downloads\setup.exe", "installers", 1000, days_old=120)

    suggestions = suggest_old_installers([node], now=_NOW)

    assert len(suggestions) == 1
    assert suggestions[0].kind == "old_installer"


def test_recent_installer_in_downloads_is_not_suggested() -> None:
    node = _node(r"C:\Users\x\Downloads\setup.exe", "installers", 1000, days_old=5)

    assert suggest_old_installers([node], now=_NOW) == []


def test_installer_outside_downloads_is_not_suggested() -> None:
    node = _node(r"C:\Program Files\App\setup.exe", "installers", 1000, days_old=120)

    assert suggest_old_installers([node], now=_NOW) == []


def test_old_file_outside_temp_folder_is_not_a_temp_suggestion() -> None:
    node = _node(r"C:\Users\x\Documents\notes.txt", "documents", 1000, days_old=30)

    assert suggest_temp_files([node], now=_NOW) == []


def test_locked_temp_file_is_never_suggested(tmp_path: Path) -> None:
    locked_dir = tmp_path / "Temp"
    locked_dir.mkdir()
    locked_file = locked_dir / "cache.tmp"
    locked_file.write_bytes(b"x")

    import win32con
    import win32file

    handle = win32file.CreateFile(
        str(locked_file),
        win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        0,
        None,
        win32con.OPEN_EXISTING,
        0,
        None,
    )
    try:
        stat = locked_file.stat()
        node = FileNode(
            path=locked_file,
            logical_size=stat.st_size,
            size_on_disk=stat.st_size,
            modified_at=_NOW - timedelta(days=30),
            category="other",
        )
        suggestions = suggest_temp_files([node], now=_NOW)
    finally:
        win32file.CloseHandle(handle)

    assert suggestions == []


def test_stale_large_file_above_threshold_is_suggested() -> None:
    node = _node(r"C:\Videos\old_movie.mp4", "videos", 200 * 1024 * 1024, days_old=400)

    suggestions = suggest_stale_large_files([node], now=_NOW)

    assert len(suggestions) == 1
    assert suggestions[0].kind == "stale_large_file"


def test_small_old_file_is_not_a_stale_large_file_suggestion() -> None:
    node = _node(r"C:\Videos\clip.mp4", "videos", 1024, days_old=400)

    assert suggest_stale_large_files([node], now=_NOW) == []


def test_duplicate_suggestions_exclude_the_suggested_keep() -> None:
    keep = _node(r"C:\Keep\file.txt", "documents", 500, days_old=10)
    extra = _node(r"C:\Extra\file.txt", "documents", 500, days_old=10)
    group = DuplicateGroup(
        size_bytes=500, files=[keep, extra], suggested_keep=keep.path, recoverable_bytes=500
    )

    suggestions = suggest_from_duplicates([group])

    assert len(suggestions) == 1
    assert suggestions[0].path == extra.path
