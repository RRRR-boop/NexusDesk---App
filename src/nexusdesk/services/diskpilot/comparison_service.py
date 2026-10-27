"""Comparaison entre deux scans d'une même racine (section 11)."""

from __future__ import annotations

from nexusdesk.models.diskpilot_domain import ComparisonResult, FileNode


def compare_scans(before: list[FileNode], after: list[FileNode]) -> ComparisonResult:
    before_by_path = {node.path: node for node in before}
    after_by_path = {node.path: node for node in after}

    added = [path for path in after_by_path if path not in before_by_path]
    removed = [path for path in before_by_path if path not in after_by_path]
    grown = [
        (path, before_by_path[path].logical_size, after_by_path[path].logical_size)
        for path in after_by_path
        if path in before_by_path
        and after_by_path[path].logical_size != before_by_path[path].logical_size
    ]
    size_delta = sum(node.logical_size for node in after) - sum(
        node.logical_size for node in before
    )

    return ComparisonResult(added=added, removed=removed, grown=grown, size_delta=size_delta)
