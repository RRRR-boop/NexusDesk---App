from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nexusdesk.models.diskpilot_domain import FileNode
from nexusdesk.services.diskpilot.comparison_service import compare_scans

_NOW = datetime(2026, 10, 27)


def _node(path: str, size: int) -> FileNode:
    return FileNode(
        path=Path(path), logical_size=size, size_on_disk=size, modified_at=_NOW, category="other"
    )


def test_added_removed_and_grown_are_detected() -> None:
    before = [_node(r"C:\a.txt", 100), _node(r"C:\b.txt", 200)]
    after = [_node(r"C:\a.txt", 150), _node(r"C:\c.txt", 50)]

    result = compare_scans(before, after)

    assert result.added == [Path(r"C:\c.txt")]
    assert result.removed == [Path(r"C:\b.txt")]
    assert result.grown == [(Path(r"C:\a.txt"), 100, 150)]
    assert result.size_delta == (150 + 50) - (100 + 200)


def test_identical_scans_report_no_changes() -> None:
    files = [_node(r"C:\a.txt", 100)]

    result = compare_scans(files, files)

    assert result.added == []
    assert result.removed == []
    assert result.grown == []
    assert result.size_delta == 0
