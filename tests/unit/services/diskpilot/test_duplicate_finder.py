from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nexusdesk.core.tasks import CancellationToken
from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.session import make_session_factory
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.diskpilot_cache import CacheBase
from nexusdesk.models.diskpilot_domain import FileNode
from nexusdesk.repositories.diskpilot_hash_cache_repository import DiskPilotHashCacheRepository
from nexusdesk.services.diskpilot.duplicate_finder import find_duplicates


def _build_cache(tmp_path: Path) -> DiskPilotHashCacheRepository:
    engine = create_sqlite_engine(tmp_path / "cache.db")
    CacheBase.metadata.create_all(engine)
    session_factory = make_session_factory(engine)
    return DiskPilotHashCacheRepository(session_factory, WriteQueue(session_factory))


def _file_node(path: Path, content: bytes) -> FileNode:
    path.write_bytes(content)
    stat = path.stat()
    return FileNode(
        path=path,
        logical_size=stat.st_size,
        size_on_disk=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        category="documents",
    )


def test_identical_content_is_grouped_as_duplicate(tmp_path: Path) -> None:
    cache = _build_cache(tmp_path)
    a = _file_node(tmp_path / "a.txt", b"contenu identique" * 100)
    b = _file_node(tmp_path / "b.txt", b"contenu identique" * 100)
    c = _file_node(tmp_path / "c.txt", b"contenu totalement different" * 100)

    groups = find_duplicates([a, b, c], min_size=1, cache=cache, token=CancellationToken())

    assert len(groups) == 1
    assert {f.path for f in groups[0].files} == {a.path, b.path}
    assert groups[0].recoverable_bytes == a.logical_size


def test_same_size_different_content_is_not_a_duplicate(tmp_path: Path) -> None:
    cache = _build_cache(tmp_path)
    a = _file_node(tmp_path / "a.txt", b"AAAAAAAAAA")
    b = _file_node(tmp_path / "b.txt", b"BBBBBBBBBB")

    groups = find_duplicates([a, b], min_size=1, cache=cache, token=CancellationToken())

    assert groups == []


def test_files_below_min_size_are_ignored(tmp_path: Path) -> None:
    cache = _build_cache(tmp_path)
    a = _file_node(tmp_path / "a.txt", b"petit")
    b = _file_node(tmp_path / "b.txt", b"petit")

    groups = find_duplicates([a, b], min_size=1_048_576, cache=cache, token=CancellationToken())

    assert groups == []


def test_onedrive_placeholder_is_never_hashed(tmp_path: Path) -> None:
    cache = _build_cache(tmp_path)
    a = _file_node(tmp_path / "a.txt", b"contenu" * 100)
    placeholder_path = tmp_path / "placeholder.txt"
    placeholder_path.write_bytes(b"contenu" * 100)
    placeholder_stat = placeholder_path.stat()
    placeholder = FileNode(
        path=placeholder_path,
        logical_size=placeholder_stat.st_size,
        size_on_disk=placeholder_stat.st_size,
        modified_at=datetime.fromtimestamp(placeholder_stat.st_mtime),
        category="documents",
        is_onedrive_placeholder=True,
    )

    groups = find_duplicates([a, placeholder], min_size=1, cache=cache, token=CancellationToken())

    assert groups == []


def test_hash_cache_is_reused_on_second_call(tmp_path: Path) -> None:
    cache = _build_cache(tmp_path)
    a = _file_node(tmp_path / "a.txt", b"contenu identique" * 100)
    b = _file_node(tmp_path / "b.txt", b"contenu identique" * 100)

    find_duplicates([a, b], min_size=1, cache=cache, token=CancellationToken())
    cached = cache.get(str(a.path), a.logical_size, a.modified_at.timestamp())

    assert cached is not None
    assert cached.full_sha256 is not None
