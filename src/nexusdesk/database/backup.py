"""Sauvegarde et vérification d'intégrité SQLite (section 14).

Une base en mode WAL ne doit **jamais** être sauvegardée par une copie de fichier brute :
le contenu peut être réparti entre le fichier principal et les fichiers ``-wal``/``-shm``,
ce qui produirait une copie incohérente. L'API native ``sqlite3.Connection.backup`` effectue
un checkpoint cohérent avant de copier.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def backup_database(source_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    source_conn = sqlite3.connect(str(source_path))
    try:
        destination_conn = sqlite3.connect(str(destination_path))
        try:
            source_conn.backup(destination_conn)
        finally:
            destination_conn.close()
    finally:
        source_conn.close()


def check_integrity(db_path: Path) -> bool:
    """Ouvre la base en lecture seule et exécute ``PRAGMA integrity_check``."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        return row is not None and row[0] == "ok"
    finally:
        conn.close()
