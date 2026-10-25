from __future__ import annotations

from pathlib import Path

from nexusdesk.database.engine import create_sqlite_engine


def test_pragmas_applied_on_every_connection(tmp_path: Path) -> None:
    engine = create_sqlite_engine(tmp_path / "test.db")
    try:
        with engine.connect() as connection:
            journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar()
            foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()
            busy_timeout = connection.exec_driver_sql("PRAGMA busy_timeout").scalar()
            synchronous = connection.exec_driver_sql("PRAGMA synchronous").scalar()

        assert journal_mode == "wal"
        assert foreign_keys == 1
        assert busy_timeout == 5000
        assert synchronous == 1  # NORMAL
    finally:
        engine.dispose()
