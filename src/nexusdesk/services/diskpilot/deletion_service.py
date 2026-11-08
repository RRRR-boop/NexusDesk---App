"""Suppression DiskPilot (section 11) : revérification pré-suppression, règles de refus,
délégation au port ``SendToRecycleBin`` (jamais d'appel Windows direct depuis ``services/``).
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from nexusdesk.models.diskpilot_domain import DeletionPreview, DeletionReport
from nexusdesk.services.diskpilot.exclusions import (
    build_excluded_paths,
    is_excluded,
    is_system_file,
)
from nexusdesk.services.diskpilot.ports import SendToRecycleBin


def build_preview(
    paths: Sequence[Path],
    expected_sizes: dict[Path, int],
    expected_mtimes: dict[Path, float],
) -> DeletionPreview:
    """Revérifie taille+date juste avant la suppression (section 11) ; un fichier
    modifié/déplacé/disparu depuis le scan est retiré de la sélection et signalé."""
    valid: list[Path] = []
    changed: list[Path] = []
    total = 0
    for path in paths:
        try:
            current = os.stat(path, follow_symlinks=False)
        except OSError:
            changed.append(path)
            continue
        expected_size = expected_sizes.get(path)
        expected_mtime = expected_mtimes.get(path)
        if expected_size is not None and current.st_size != expected_size:
            changed.append(path)
            continue
        if expected_mtime is not None and current.st_mtime != expected_mtime:
            changed.append(path)
            continue
        valid.append(path)
        total += current.st_size
    return DeletionPreview(valid_paths=valid, changed_paths=changed, total_size=total)


def _is_locked(path: Path) -> bool:
    try:
        with path.open("r+b"):
            return False
    except OSError:
        return True


def filter_refused(
    paths: Sequence[Path], scan_root: Path
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Refus systématique : attribut système, chemin exclu, fichier en cours d'utilisation."""
    excluded_paths = build_excluded_paths(scan_root)
    allowed: list[Path] = []
    refused: list[tuple[Path, str]] = []
    for path in paths:
        if is_system_file(path):
            refused.append((path, "Fichier système, jamais supprimable."))
        elif is_excluded(path, excluded_paths, scan_root):
            refused.append((path, "Chemin exclu par défaut."))
        elif _is_locked(path):
            refused.append((path, "Fichier en cours d'utilisation."))
        else:
            allowed.append(path)
    return allowed, refused


def execute_deletion(
    paths: Sequence[Path],
    sizes: dict[Path, int],
    scan_root: Path,
    send_to_recycle_bin: SendToRecycleBin,
) -> DeletionReport:
    allowed, failed_initial = filter_refused(paths, scan_root)
    outcomes = send_to_recycle_bin(allowed) if allowed else []
    outcome_by_path = {Path(outcome.path): outcome for outcome in outcomes}

    succeeded: list[Path] = []
    failed: list[tuple[Path, str]] = list(failed_initial)
    freed = 0
    for path in allowed:
        outcome = outcome_by_path.get(path)
        if outcome is not None and outcome.succeeded:
            succeeded.append(path)
            freed += sizes.get(path, 0)
        elif outcome is not None:
            failed.append((path, outcome.error_message or "Échec inconnu."))
        else:
            failed.append((path, "Aucun résultat renvoyé par la Corbeille."))

    return DeletionReport(succeeded=succeeded, failed=failed, freed_bytes=freed)
