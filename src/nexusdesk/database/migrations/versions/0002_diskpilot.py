"""Tables DiskPilot : scans, dossiers, plus gros fichiers, entrées ignorées, liens, doublons.

Revision ID: 0002_diskpilot
Revises: 0001_initial
Create Date: 2026-10-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002_diskpilot"
down_revision: str | None = "0001_initial"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "diskpilot_scan",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("root_path", sa.Text(), nullable=False),
        sa.Column("normalized_root_path", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dir_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_logical_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_size_on_disk", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("excluded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inaccessible_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("onedrive_placeholder_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hardlink_dedup_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("link_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("options_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_diskpilot_scan_root_started",
        "diskpilot_scan",
        ["normalized_root_path", "started_at"],
    )

    op.create_table(
        "diskpilot_folder_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "scan_id",
            sa.Integer(),
            sa.ForeignKey("diskpilot_scan.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("parent_path", sa.Text(), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("logical_size", sa.BigInteger(), nullable=False),
        sa.Column("size_on_disk", sa.BigInteger(), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False),
        sa.Column("category_sizes_json", sa.Text(), nullable=False, server_default="{}"),
        sa.UniqueConstraint("scan_id", "path"),
    )
    op.create_index(
        "ix_diskpilot_folder_snapshot_scan_parent",
        "diskpilot_folder_snapshot",
        ["scan_id", "parent_path"],
    )

    op.create_table(
        "diskpilot_largest_file",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "scan_id",
            sa.Integer(),
            sa.ForeignKey("diskpilot_scan.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("logical_size", sa.BigInteger(), nullable=False),
        sa.Column("size_on_disk", sa.BigInteger(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("is_onedrive_placeholder", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.UniqueConstraint("scan_id", "path"),
    )
    op.create_index(
        "ix_diskpilot_largest_file_scan_size",
        "diskpilot_largest_file",
        ["scan_id", "logical_size"],
    )

    op.create_table(
        "diskpilot_skipped_entry",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "scan_id",
            sa.Integer(),
            sa.ForeignKey("diskpilot_scan.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
    )
    op.create_index("ix_diskpilot_skipped_entry_scan", "diskpilot_skipped_entry", ["scan_id"])

    op.create_table(
        "diskpilot_link_entry",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "scan_id",
            sa.Integer(),
            sa.ForeignKey("diskpilot_scan.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("link_type", sa.Text(), nullable=False),
        sa.Column("target_path", sa.Text(), nullable=True),
        sa.Column("is_broken", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.create_index("ix_diskpilot_link_entry_scan", "diskpilot_link_entry", ["scan_id"])

    op.create_table(
        "diskpilot_duplicate_group",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "scan_id",
            sa.Integer(),
            sa.ForeignKey("diskpilot_scan.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False),
        sa.Column("recoverable_bytes", sa.BigInteger(), nullable=False),
        sa.Column("suggested_keep_path", sa.Text(), nullable=False),
    )

    op.create_table(
        "diskpilot_duplicate_file",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("diskpilot_duplicate_group.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.Column("is_suggested_keep", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.create_index("ix_diskpilot_duplicate_file_group", "diskpilot_duplicate_file", ["group_id"])


def downgrade() -> None:
    op.drop_table("diskpilot_duplicate_file")
    op.drop_table("diskpilot_duplicate_group")
    op.drop_table("diskpilot_link_entry")
    op.drop_table("diskpilot_skipped_entry")
    op.drop_table("diskpilot_largest_file")
    op.drop_table("diskpilot_folder_snapshot")
    op.drop_table("diskpilot_scan")
