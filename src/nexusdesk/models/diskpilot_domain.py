"""Dataclasses pures du domaine DiskPilot (section 11) — zéro Qt, zéro appel Windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

Category = Literal[
    "videos", "images", "audio", "documents", "archives", "installers", "code", "other"
]
LinkType = Literal["symlink", "junction"]
SkippedKind = Literal["excluded_default", "excluded_user", "excluded_system_file", "inaccessible"]
SkippedReason = Literal["access_denied", "path_too_long", "locked", "excluded_path"]
ScanStatus = Literal["running", "completed", "cancelled", "failed"]
CleanupKind = Literal["old_installer", "temp_file", "duplicate", "stale_large_file"]


@dataclass(frozen=True)
class ScanOptions:
    root: Path
    min_duplicate_size: int = 1_048_576  # 1 Mo, réglable (section 11)
    extra_excluded_paths: tuple[Path, ...] = ()  # exclusions personnalisées (section 15)


@dataclass
class FileNode:
    path: Path
    logical_size: int
    size_on_disk: int
    modified_at: datetime
    category: Category
    is_onedrive_placeholder: bool = False
    hardlink_key: tuple[int, int, int] | None = None


@dataclass
class FolderNode:
    path: Path
    depth: int
    files: list[FileNode] = field(default_factory=list)
    children: list[FolderNode] = field(default_factory=list)
    logical_size: int = 0
    size_on_disk: int = 0
    file_count: int = 0
    category_sizes: dict[Category, int] = field(default_factory=dict)


@dataclass(frozen=True)
class SkippedEntry:
    path: Path
    kind: SkippedKind
    reason: SkippedReason


@dataclass(frozen=True)
class LinkEntry:
    path: Path
    link_type: LinkType
    target_path: Path | None
    is_broken: bool


@dataclass
class ScanResult:
    scan_id: int
    root: FolderNode
    started_at: datetime
    finished_at: datetime
    status: ScanStatus
    file_count: int
    dir_count: int
    total_logical_size: int
    total_size_on_disk: int
    excluded_count: int
    inaccessible_count: int
    onedrive_placeholder_count: int
    hardlink_dedup_count: int
    link_count: int
    largest_files: list[FileNode]
    skipped: list[SkippedEntry]
    links: list[LinkEntry]


@dataclass(frozen=True)
class DuplicateGroup:
    size_bytes: int
    files: list[FileNode]
    suggested_keep: Path
    recoverable_bytes: int


@dataclass(frozen=True)
class CleanupSuggestion:
    kind: CleanupKind
    path: Path
    size_bytes: int
    detail: str


@dataclass(frozen=True)
class DeletionPreview:
    valid_paths: list[Path]
    changed_paths: list[Path]
    total_size: int


@dataclass(frozen=True)
class DeletionReport:
    succeeded: list[Path]
    failed: list[tuple[Path, str]]
    freed_bytes: int


@dataclass(frozen=True)
class ComparisonResult:
    added: list[Path]
    removed: list[Path]
    grown: list[tuple[Path, int, int]]
    size_delta: int


def flatten_folder_tree(root: FolderNode) -> list[FolderNode]:
    """Aplatit l'arbre en une liste (pile explicite) — utilisé à la fois par le dépôt
    (persistance ≤4 niveaux) et par les viewmodels (export CSV, navigation)."""
    flat: list[FolderNode] = []
    stack: list[FolderNode] = [root]
    while stack:
        node = stack.pop()
        flat.append(node)
        stack.extend(node.children)
    return flat
