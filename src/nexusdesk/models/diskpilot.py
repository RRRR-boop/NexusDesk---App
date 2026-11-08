"""Entités SQLAlchemy du module DiskPilot (section 11, cf. ADR-0013 pour la rétention)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from nexusdesk.models.base import Base


class DiskScan(Base):
    __tablename__ = "diskpilot_scan"
    __table_args__ = (
        Index("ix_diskpilot_scan_root_started", "normalized_root_path", "started_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    root_path: Mapped[str]
    normalized_root_path: Mapped[str]
    started_at: Mapped[datetime]
    finished_at: Mapped[datetime | None]
    status: Mapped[str]  # running|completed|cancelled|failed
    file_count: Mapped[int] = mapped_column(default=0)
    dir_count: Mapped[int] = mapped_column(default=0)
    total_logical_size: Mapped[int] = mapped_column(default=0)
    total_size_on_disk: Mapped[int] = mapped_column(default=0)
    excluded_count: Mapped[int] = mapped_column(default=0)
    inaccessible_count: Mapped[int] = mapped_column(default=0)
    onedrive_placeholder_count: Mapped[int] = mapped_column(default=0)
    hardlink_dedup_count: Mapped[int] = mapped_column(default=0)
    link_count: Mapped[int] = mapped_column(default=0)
    options_json: Mapped[str] = mapped_column(default="{}")
    error_message: Mapped[str | None]


class DiskFolderSnapshot(Base):
    __tablename__ = "diskpilot_folder_snapshot"
    __table_args__ = (
        UniqueConstraint("scan_id", "path"),
        Index("ix_diskpilot_folder_snapshot_scan_parent", "scan_id", "parent_path"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("diskpilot_scan.id", ondelete="CASCADE"))
    path: Mapped[str]
    parent_path: Mapped[str | None]
    depth: Mapped[int]
    logical_size: Mapped[int]
    size_on_disk: Mapped[int]
    file_count: Mapped[int]
    category_sizes_json: Mapped[str] = mapped_column(default="{}")


class DiskLargestFile(Base):
    __tablename__ = "diskpilot_largest_file"
    __table_args__ = (
        UniqueConstraint("scan_id", "path"),
        Index("ix_diskpilot_largest_file_scan_size", "scan_id", "logical_size"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("diskpilot_scan.id", ondelete="CASCADE"))
    path: Mapped[str]
    logical_size: Mapped[int]
    size_on_disk: Mapped[int]
    modified_at: Mapped[datetime]
    category: Mapped[str]
    is_onedrive_placeholder: Mapped[bool] = mapped_column(default=False)
    rank: Mapped[int]


class DiskSkippedEntry(Base):
    __tablename__ = "diskpilot_skipped_entry"
    __table_args__ = (Index("ix_diskpilot_skipped_entry_scan", "scan_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("diskpilot_scan.id", ondelete="CASCADE"))
    path: Mapped[str]
    kind: Mapped[str]  # excluded_default|excluded_user|excluded_system_file|inaccessible
    reason: Mapped[str]  # access_denied|path_too_long|locked|excluded_path


class DiskLinkEntry(Base):
    __tablename__ = "diskpilot_link_entry"
    __table_args__ = (Index("ix_diskpilot_link_entry_scan", "scan_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("diskpilot_scan.id", ondelete="CASCADE"))
    path: Mapped[str]
    link_type: Mapped[str]  # symlink|junction
    target_path: Mapped[str | None]
    is_broken: Mapped[bool] = mapped_column(default=False)


class DiskDuplicateGroup(Base):
    __tablename__ = "diskpilot_duplicate_group"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("diskpilot_scan.id", ondelete="CASCADE"))
    size_bytes: Mapped[int]
    file_count: Mapped[int]
    recoverable_bytes: Mapped[int]
    suggested_keep_path: Mapped[str]


class DiskDuplicateFile(Base):
    __tablename__ = "diskpilot_duplicate_file"
    __table_args__ = (Index("ix_diskpilot_duplicate_file_group", "group_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("diskpilot_duplicate_group.id", ondelete="CASCADE")
    )
    path: Mapped[str]
    modified_at: Mapped[datetime]
    is_suggested_keep: Mapped[bool] = mapped_column(default=False)
