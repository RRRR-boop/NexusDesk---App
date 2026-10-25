"""Invocation programmatique d'Alembic au démarrage (section 14).

Procédure imposée par le cahier des charges : si une migration est nécessaire, une
sauvegarde cohérente est prise et vérifiée (``PRAGMA integrity_check``) avant la tentative ;
en cas d'échec de la migration, la sauvegarde est restaurée et l'application démarre en
lecture seule plutôt que de risquer de perdre des données.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine

from nexusdesk.database.backup import backup_database, check_integrity

_logger = logging.getLogger("nexusdesk.database.migration")

_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@dataclass(frozen=True)
class MigrationResult:
    applied: bool
    read_only: bool
    message: str


def _build_config(db_path: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _current_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()


def ensure_up_to_date(engine: Engine, db_path: Path, backups_dir: Path) -> MigrationResult:
    """Met la base à jour si nécessaire ; ne lève jamais, renvoie un résultat typé."""
    config = _build_config(db_path)
    script_directory = ScriptDirectory.from_config(config)
    head_revision = script_directory.get_current_head()
    current_revision = _current_revision(engine)

    if current_revision == head_revision:
        return MigrationResult(applied=False, read_only=False, message="Base à jour.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backups_dir / f"pre-migration-{db_path.stem}-{timestamp}.db"
    backup_database(db_path, backup_path)

    if not check_integrity(backup_path):
        _logger.error(
            "La vérification d'intégrité de la sauvegarde pré-migration de %s a échoué.",
            db_path.name,
        )
        return MigrationResult(
            applied=False,
            read_only=True,
            message="La sauvegarde pré-migration n'a pas passé le contrôle d'intégrité ; "
            "démarrage en lecture seule pour ne pas risquer de perdre des données.",
        )

    try:
        command.upgrade(config, "head")
    except Exception as exc:
        _logger.exception(
            "Échec de la migration de %s, restauration de la sauvegarde.", db_path.name
        )
        engine.dispose()
        shutil.copyfile(backup_path, db_path)
        return MigrationResult(
            applied=False,
            read_only=True,
            message=f"La migration a échoué et a été annulée ; démarrage en lecture seule ({exc}).",
        )

    return MigrationResult(
        applied=True, read_only=False, message="Migration appliquée avec succès."
    )
