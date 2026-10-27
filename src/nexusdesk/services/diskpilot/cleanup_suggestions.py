"""Suggestions de nettoyage (section 11) : présentées comme des pistes à vérifier, jamais
comme des fichiers « inutiles »."""

from __future__ import annotations

from datetime import datetime, timedelta

from nexusdesk.models.diskpilot_domain import CleanupSuggestion, DuplicateGroup, FileNode

_OLD_INSTALLER_DAYS = 90
_TEMP_FILE_DAYS = 7
_STALE_LARGE_FILE_DAYS = 365
_STALE_LARGE_FILE_MIN_SIZE = 100 * 1024 * 1024  # 100 Mo
_DOWNLOADS_FOLDER_NAMES = {"téléchargements", "downloads"}


def _parts_lower(node: FileNode) -> set[str]:
    return {part.lower() for part in node.path.parts}


def suggest_old_installers(
    files: list[FileNode], now: datetime | None = None
) -> list[CleanupSuggestion]:
    now = now or datetime.now()
    threshold = now - timedelta(days=_OLD_INSTALLER_DAYS)
    suggestions: list[CleanupSuggestion] = []
    for node in files:
        if node.category != "installers":
            continue
        if not (_parts_lower(node) & _DOWNLOADS_FOLDER_NAMES):
            continue
        if node.modified_at < threshold:
            suggestions.append(
                CleanupSuggestion(
                    kind="old_installer",
                    path=node.path,
                    size_bytes=node.logical_size,
                    detail=(
                        f"Installateur non modifié depuis plus de {_OLD_INSTALLER_DAYS} "
                        "jours dans Téléchargements."
                    ),
                )
            )
    return suggestions


def suggest_temp_files(
    files: list[FileNode], now: datetime | None = None
) -> list[CleanupSuggestion]:
    now = now or datetime.now()
    threshold = now - timedelta(days=_TEMP_FILE_DAYS)
    suggestions: list[CleanupSuggestion] = []
    for node in files:
        if "temp" not in _parts_lower(node):
            continue
        if node.modified_at >= threshold:
            continue
        try:
            with node.path.open("r+b"):
                pass
        except OSError:
            continue  # verrouillé : jamais suggéré (section 11)
        suggestions.append(
            CleanupSuggestion(
                kind="temp_file",
                path=node.path,
                size_bytes=node.logical_size,
                detail=f"Fichier temporaire non modifié depuis plus de {_TEMP_FILE_DAYS} jours.",
            )
        )
    return suggestions


def suggest_stale_large_files(
    files: list[FileNode], now: datetime | None = None
) -> list[CleanupSuggestion]:
    now = now or datetime.now()
    threshold = now - timedelta(days=_STALE_LARGE_FILE_DAYS)
    return [
        CleanupSuggestion(
            kind="stale_large_file",
            path=node.path,
            size_bytes=node.logical_size,
            detail="Gros fichier non modifié depuis plus d'un an.",
        )
        for node in files
        if node.logical_size >= _STALE_LARGE_FILE_MIN_SIZE and node.modified_at < threshold
    ]


def suggest_from_duplicates(groups: list[DuplicateGroup]) -> list[CleanupSuggestion]:
    suggestions: list[CleanupSuggestion] = []
    for group in groups:
        for file_node in group.files:
            if file_node.path == group.suggested_keep:
                continue
            suggestions.append(
                CleanupSuggestion(
                    kind="duplicate",
                    path=file_node.path,
                    size_bytes=group.size_bytes,
                    detail=(
                        f"Doublon de {group.suggested_keep.name} ({len(group.files)} exemplaires)."
                    ),
                )
            )
    return suggestions
