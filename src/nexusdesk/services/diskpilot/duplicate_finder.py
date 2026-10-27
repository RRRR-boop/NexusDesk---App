"""Détection de doublons (section 11) : taille exacte -> empreinte partielle -> complète.

Les fichiers OneDrive à la demande (``is_onedrive_placeholder``) sont exclus dès le
regroupement par taille — jamais un ``open()`` sur ces chemins, pour ne jamais déclencher
leur téléchargement. Les empreintes sont mises en cache par (chemin, taille, date de
modification) via le dépôt dédié (``repositories/`` est une importation directe autorisée
pour ``services/``, pas besoin d'injection de port ici).
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from nexusdesk.core.tasks import CancellationToken
from nexusdesk.models.diskpilot_domain import DuplicateGroup, FileNode
from nexusdesk.repositories.diskpilot_hash_cache_repository import (
    DiskPilotHashCacheRepository,
)

_PARTIAL_CHUNK_SIZE = 64 * 1024
_FULL_READ_CHUNK_SIZE = 1024 * 1024


def _partial_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    size = path.stat().st_size
    with path.open("rb") as handle:
        hasher.update(handle.read(_PARTIAL_CHUNK_SIZE))
        if size > _PARTIAL_CHUNK_SIZE:
            handle.seek(max(size - _PARTIAL_CHUNK_SIZE, 0))
            hasher.update(handle.read(_PARTIAL_CHUNK_SIZE))
    return hasher.hexdigest()


def _full_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_FULL_READ_CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _cached_or_compute(
    node: FileNode,
    cache: DiskPilotHashCacheRepository,
    kind: Literal["partial", "full"],
    compute: Callable[[Path], str],
) -> str:
    mtime = node.modified_at.timestamp()
    path_text = str(node.path)
    cached = cache.get(path_text, node.logical_size, mtime)
    if cached is not None:
        existing = cached.partial_sha256 if kind == "partial" else cached.full_sha256
        if existing is not None:
            return existing
    digest = compute(node.path)
    cache.upsert(path_text, node.logical_size, mtime, kind, digest)
    return digest


def find_duplicates(
    files: list[FileNode],
    min_size: int,
    cache: DiskPilotHashCacheRepository,
    token: CancellationToken,
) -> list[DuplicateGroup]:
    size_groups: dict[int, list[FileNode]] = defaultdict(list)
    for file_node in files:
        if file_node.is_onedrive_placeholder:
            continue  # jamais haché (section 11)
        if file_node.logical_size >= min_size:
            size_groups[file_node.logical_size].append(file_node)

    groups: list[DuplicateGroup] = []
    for candidates in size_groups.values():
        if len(candidates) < 2:
            continue
        token.raise_if_cancelled()
        groups.extend(_find_duplicates_within_size_group(candidates, cache, token))

    return groups


def _find_duplicates_within_size_group(
    candidates: list[FileNode],
    cache: DiskPilotHashCacheRepository,
    token: CancellationToken,
) -> list[DuplicateGroup]:
    partial_groups: dict[str, list[FileNode]] = defaultdict(list)
    for node in candidates:
        try:
            digest = _cached_or_compute(node, cache, "partial", _partial_hash)
        except OSError:
            continue
        partial_groups[digest].append(node)

    groups: list[DuplicateGroup] = []
    for partial_candidates in partial_groups.values():
        if len(partial_candidates) < 2:
            continue
        token.raise_if_cancelled()

        full_groups: dict[str, list[FileNode]] = defaultdict(list)
        for node in partial_candidates:
            try:
                digest = _cached_or_compute(node, cache, "full", _full_hash)
            except OSError:
                continue
            full_groups[digest].append(node)

        for full_candidates in full_groups.values():
            if len(full_candidates) >= 2:
                groups.append(_build_group(full_candidates))

    return groups


def _build_group(nodes: list[FileNode]) -> DuplicateGroup:
    def _sort_key(node: FileNode) -> tuple[int, float]:
        in_downloads = any(part.lower() == "téléchargements" for part in node.path.parts) or any(
            part.lower() == "downloads" for part in node.path.parts
        )
        return (1 if in_downloads else 0, node.modified_at.timestamp())

    sorted_nodes = sorted(nodes, key=_sort_key)
    size = nodes[0].logical_size
    return DuplicateGroup(
        size_bytes=size,
        files=nodes,
        suggested_keep=sorted_nodes[0].path,
        recoverable_bytes=size * (len(nodes) - 1),
    )
