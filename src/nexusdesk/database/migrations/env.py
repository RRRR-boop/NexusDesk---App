"""Environnement Alembic invoqué programmatiquement par ``migration_runner.py``.

Aucun fichier ``alembic.ini`` n'est lu : la configuration (URL de la base, emplacement des
scripts) est injectée en mémoire par l'appelant via ``alembic.config.Config``.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from nexusdesk.models.base import Base
from nexusdesk.models.settings import SettingRow  # noqa: F401 - enregistre la table dans Base.metadata

config = context.config

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
