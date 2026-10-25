"""Vérifie le critère de sortie « migrations et sauvegardes testées » (section 14) :
en cas d'échec de migration, les données déjà présentes sont intégralement restaurées et
l'application est censée démarrer en lecture seule plutôt que de perdre des données.
"""

from __future__ import annotations

from pathlib import Path

from alembic.script import ScriptDirectory

from nexusdesk.database import migration_runner
from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.migration_runner import ensure_up_to_date


def _raise_simulated_failure(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("Échec simulé de la migration")


def test_failed_migration_restores_existing_data(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "nexusdesk.db"
    backups_dir = tmp_path / "backups"

    engine = create_sqlite_engine(db_path)
    try:
        # Première migration réelle, puis on écrit une donnée à protéger.
        first_result = ensure_up_to_date(engine, db_path, backups_dir)
        assert first_result.applied is True

        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO settings (key, value, updated_at) "
                "VALUES ('probe', '\"precieux\"', '2026-01-01 00:00:00')"
            )

        # Fait croire à ensure_up_to_date qu'une migration est en attente, puis force
        # l'échec réel de l'upgrade (un script de migration défaillant produirait le même
        # effet : la résolution interne d'Alembic n'est pas ce qu'on veut tester ici).
        monkeypatch.setattr(ScriptDirectory, "get_current_head", lambda self: "9999_fake")
        monkeypatch.setattr(migration_runner.command, "upgrade", _raise_simulated_failure)

        second_result = ensure_up_to_date(engine, db_path, backups_dir)

        assert second_result.applied is False
        assert second_result.read_only is True

        # Deux sauvegardes au total : une pour la migration initiale, une avant la tentative
        # échouée.
        assert len(list(backups_dir.glob("*.db"))) == 2
    finally:
        engine.dispose()

    # La restauration remet le fichier vivant dans l'état d'avant la tentative échouée :
    # la donnée protégée doit toujours être présente, intacte.
    restored_engine = create_sqlite_engine(db_path)
    try:
        with restored_engine.connect() as connection:
            row = connection.exec_driver_sql(
                "SELECT value FROM settings WHERE key = 'probe'"
            ).fetchone()
        assert row is not None
        assert row[0] == '"precieux"'
    finally:
        restored_engine.dispose()
