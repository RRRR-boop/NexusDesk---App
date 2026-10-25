"""Résolution des chemins de données, en tenant compte du mode portable.

Toutes les autres couches (logging, base de données, diagnostics) obtiennent leurs
emplacements via ce module plutôt que de construire des chemins elles-mêmes, afin que le
mode portable (fichier ``portable.flag`` à côté de l'exécutable) s'applique uniformément.
"""

from __future__ import annotations

import sys
from pathlib import Path

from nexusdesk.core.errors import PermissionDenied

_APP_NAME = "NexusDesk"
_PORTABLE_FLAG_NAME = "portable.flag"


def _executable_dir() -> Path:
    """Dossier de l'exécutable (mode packagé) ou racine du dépôt (mode développeur)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # En mode développeur, la racine du dépôt est trois niveaux au-dessus de ce fichier
    # (src/nexusdesk/core/paths.py -> src/nexusdesk/core -> src/nexusdesk -> src -> racine).
    return Path(__file__).resolve().parents[3]


def is_portable() -> bool:
    """Vrai si un fichier ``portable.flag`` est présent à côté de l'exécutable."""
    return (_executable_dir() / _PORTABLE_FLAG_NAME).exists()


def get_app_root() -> Path:
    """Racine de toutes les données NexusDesk (portable ou %LOCALAPPDATA%)."""
    if is_portable():
        return _executable_dir() / "NexusDeskData"
    local_app_data = Path.home() / "AppData" / "Local"
    return local_app_data / _APP_NAME


def _ensure_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PermissionDenied(f"Impossible de créer le dossier {path} : {exc}") from exc
    return path


def get_data_dir() -> Path:
    return _ensure_dir(get_app_root() / "data")


def get_backups_dir() -> Path:
    return _ensure_dir(get_app_root() / "backups")


def get_logs_dir() -> Path:
    return _ensure_dir(get_app_root() / "logs")


def get_tessdata_dir() -> Path:
    return _ensure_dir(get_app_root() / "tessdata")


def get_cache_dir() -> Path:
    return _ensure_dir(get_app_root() / "cache")
