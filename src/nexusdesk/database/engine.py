"""Création des moteurs SQLAlchemy et réglages SQLite obligatoires (section 14)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event


def _apply_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


def create_sqlite_engine(db_path: Path) -> Engine:
    """Crée un moteur SQLite avec WAL/foreign_keys/busy_timeout/synchronous sur chaque connexion."""
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    event.listen(engine, "connect", _apply_pragmas)
    return engine
