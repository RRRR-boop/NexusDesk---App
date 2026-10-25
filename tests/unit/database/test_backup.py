from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from nexusdesk.database.backup import backup_database, check_integrity
from nexusdesk.database.engine import create_sqlite_engine


def test_backup_preserves_data_written_under_wal(tmp_path: Path) -> None:
    db_path = tmp_path / "source.db"
    backup_path = tmp_path / "backup.db"

    engine = create_sqlite_engine(db_path)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE t (value TEXT)")
            connection.exec_driver_sql("INSERT INTO t (value) VALUES ('hello')")

        backup_database(db_path, backup_path)
        assert check_integrity(backup_path) is True

        with sqlite3.connect(str(backup_path)) as conn:
            row = conn.execute("SELECT value FROM t").fetchone()
        assert row == ("hello",)
    finally:
        engine.dispose()


def test_check_integrity_raises_for_a_non_sqlite_file(tmp_path: Path) -> None:
    db_path = tmp_path / "broken.db"
    db_path.write_bytes(b"ceci n'est pas une base SQLite")

    with pytest.raises(sqlite3.DatabaseError):
        check_integrity(db_path)
