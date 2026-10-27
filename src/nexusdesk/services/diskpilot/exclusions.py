"""Exclusions par défaut (section 11) : fonctions pures, zéro appel Windows.

La racine choisie par l'utilisateur est exemptée de sa propre règle d'exclusion (scan
explicite autorisé, avec avertissement côté UI) ; les exclusions système imbriquées
restent actives pour tout chemin différent de la racine.
"""

from __future__ import annotations

import os
from pathlib import Path

_SYSTEM_FILE_NAMES = frozenset({"pagefile.sys", "hiberfil.sys", "swapfile.sys"})

_PER_VOLUME_EXCLUDED_NAMES = ("$Recycle.Bin", "System Volume Information", "Recovery")
_SYSTEM_DRIVE_EXCLUDED_NAMES = (
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "ProgramData",
)


def is_system_file(path: Path) -> bool:
    """Fichiers système jamais supprimables (section 11), affichés comme tels."""
    return path.name.lower() in _SYSTEM_FILE_NAMES


def build_excluded_paths(scan_root: Path) -> set[Path]:
    """Chemins absolus exclus par défaut pour un scan de ``scan_root`` : les dossiers
    système du volume contenant la racine, et en plus les dossiers Windows/Program Files
    si ce volume est le volume système."""
    drive = scan_root.resolve().drive
    excluded = {Path(drive + "\\" + name) for name in _PER_VOLUME_EXCLUDED_NAMES}

    system_drive = os.environ.get("SYSTEMDRIVE", "C:")
    if drive.upper() == system_drive.upper():
        excluded |= {Path(drive + "\\" + name) for name in _SYSTEM_DRIVE_EXCLUDED_NAMES}

    return excluded


def is_excluded(path: Path, excluded_paths: set[Path], scan_root: Path) -> bool:
    resolved = path.resolve()
    if resolved == scan_root.resolve():
        return False
    return any(resolved == excluded or excluded in resolved.parents for excluded in excluded_paths)
