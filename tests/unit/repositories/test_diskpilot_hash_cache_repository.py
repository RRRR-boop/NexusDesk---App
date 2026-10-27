from __future__ import annotations

from pathlib import Path

from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.session import make_session_factory
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.diskpilot_cache import CacheBase
from nexusdesk.repositories.diskpilot_hash_cache_repository import DiskPilotHashCacheRepository


def _build_repository(tmp_path: Path) -> DiskPilotHashCacheRepository:
    engine = create_sqlite_engine(tmp_path / "cache.db")
    CacheBase.metadata.create_all(engine)
    session_factory = make_session_factory(engine)
    return DiskPilotHashCacheRepository(session_factory, WriteQueue(session_factory))


def test_get_returns_none_for_unknown_path(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)

    assert repository.get(r"C:\inconnu.txt", size=10, mtime=100.0) is None


def test_upsert_then_get_round_trips(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)

    repository.upsert(r"C:\a.txt", size=10, mtime=100.0, kind="partial", digest="abc")
    cached = repository.get(r"C:\a.txt", size=10, mtime=100.0)

    assert cached is not None
    assert cached.partial_sha256 == "abc"
    assert cached.full_sha256 is None


def test_get_is_invalidated_when_size_changes(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)
    repository.upsert(r"C:\a.txt", size=10, mtime=100.0, kind="full", digest="abc")

    assert repository.get(r"C:\a.txt", size=999, mtime=100.0) is None


def test_get_is_invalidated_when_mtime_changes(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)
    repository.upsert(r"C:\a.txt", size=10, mtime=100.0, kind="full", digest="abc")

    assert repository.get(r"C:\a.txt", size=10, mtime=999.0) is None


def test_upsert_overwrites_stale_entry_for_changed_file(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)
    repository.upsert(r"C:\a.txt", size=10, mtime=100.0, kind="full", digest="old-digest")

    # Le fichier a change (nouvelle taille/date) : une nouvelle empreinte remplace l'ancienne
    # plutot que de laisser une ligne perimee associee au meme chemin.
    repository.upsert(r"C:\a.txt", size=20, mtime=200.0, kind="full", digest="new-digest")

    cached = repository.get(r"C:\a.txt", size=20, mtime=200.0)
    assert cached is not None
    assert cached.full_sha256 == "new-digest"
