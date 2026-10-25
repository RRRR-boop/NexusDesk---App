from __future__ import annotations

from pathlib import Path

from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.migration_runner import ensure_up_to_date


def test_initial_migration_creates_settings_table(tmp_path: Path) -> None:
    db_path = tmp_path / "nexusdesk.db"
    backups_dir = tmp_path / "backups"

    engine = create_sqlite_engine(db_path)
    try:
        result = ensure_up_to_date(engine, db_path, backups_dir)

        assert result.applied is True
        assert result.read_only is False

        with engine.connect() as connection:
            tables = {
                row[0]
                for row in connection.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert "settings" in tables
        assert "alembic_version" in tables

        # Sauvegarde prise avant la migration, même pour une base vide (section 14).
        assert len(list(backups_dir.glob("*.db"))) == 1
    finally:
        engine.dispose()


def test_second_call_is_a_noop(tmp_path: Path) -> None:
    db_path = tmp_path / "nexusdesk.db"
    backups_dir = tmp_path / "backups"
    engine = create_sqlite_engine(db_path)
    try:
        ensure_up_to_date(engine, db_path, backups_dir)
        result = ensure_up_to_date(engine, db_path, backups_dir)

        assert result.applied is False
        assert result.read_only is False
        assert len(list(backups_dir.glob("*.db"))) == 1  # pas de nouvelle sauvegarde
    finally:
        engine.dispose()
