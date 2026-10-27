"""Appels Windows nécessaires à DiskPilot (section 11) : taille sur disque, identité de
fichier pour les liens physiques, volumes, Corbeille, ouverture de l'Explorateur.

``send_to_recycle_bin`` utilise ``SHFileOperation`` plutôt que l'interface COM moderne
``IFileOperation`` citée par le cahier des charges : voir ADR-0010 pour la justification
(même résultat observable — suppression récupérable —, sans nouvelle dépendance).
"""

from __future__ import annotations

import logging
import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import psutil
import pywintypes
import win32api
import win32con
import win32file
from win32com.shell import shell, shellcon

_logger = logging.getLogger("nexusdesk.integrations.filesystem")

VolumeType = Literal["fixed", "removable", "network", "optical", "unknown"]

_DRIVE_TYPE_MAP: dict[int, VolumeType] = {
    win32con.DRIVE_FIXED: "fixed",
    win32con.DRIVE_REMOVABLE: "removable",
    win32con.DRIVE_REMOTE: "network",
    win32con.DRIVE_CDROM: "optical",
}


@dataclass(frozen=True)
class VolumeInfo:
    letter: str
    label: str
    filesystem: str
    volume_type: VolumeType
    total_bytes: int
    used_bytes: int
    free_bytes: int


@dataclass(frozen=True)
class DeletionOutcome:
    path: str
    succeeded: bool
    error_message: str | None


def _long_path(path: Path) -> str:
    """Préfixe ``\\\\?\\`` pour les chemins longs, indépendamment du réglage registre
    ``LongPathsEnabled`` (section 16)."""
    text = str(path)
    if text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def get_size_on_disk(path: Path) -> int:
    """Taille réelle sur disque (compression NTFS, fichiers creux). Lève OSError si échec."""
    try:
        # Stub incomplet (signature/typage) pour cette fonction win32file ; comportement
        # réel vérifié manuellement (renvoie un int).
        return win32file.GetCompressedFileSize(_long_path(path))  # type: ignore[no-any-return,no-untyped-call,call-arg]
    except pywintypes.error as exc:
        raise OSError(exc.winerror, exc.strerror, str(path)) from exc


def get_hardlink_key(path: Path) -> tuple[int, int, int] | None:
    """Identité stable (volume, index haut, index bas) pour détecter les liens physiques.

    Coûteuse (ouvre un handle) : n'est censée être appelée que lorsque
    ``os.stat(path).st_nlink > 1`` — stratégie mesurée empiriquement, voir ADR-0011.
    Renvoie ``None`` si indéterminable (mieux ne pas dédupliquer que dédupliquer à tort).
    """
    try:
        handle = win32file.CreateFile(
            _long_path(path),
            win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )
    except pywintypes.error:
        return None
    try:
        # Les stubs typent le handle retourné (PyHANDLE) comme incompatible avec les
        # paramètres "int" déclarés ici ; limitation connue des stubs (cf. lot 0).
        info = win32file.GetFileInformationByHandle(handle)  # type: ignore[arg-type]
    except pywintypes.error:
        return None
    finally:
        win32file.CloseHandle(handle)  # type: ignore[arg-type]
    volume_serial, _size_high, _size_low, _links, index_high, index_low = info[4:10]
    return (volume_serial, index_high, index_low)


def list_volumes() -> list[VolumeInfo]:
    """Un volume illisible (lecteur optique vide...) est omis, jamais une ligne fantôme."""
    volumes: list[VolumeInfo] = []
    for partition in psutil.disk_partitions(all=False):
        letter = partition.mountpoint
        try:
            usage = psutil.disk_usage(letter)
            label, _serial, _max_len, _flags, filesystem = win32api.GetVolumeInformation(letter)
            drive_type_code = win32file.GetDriveType(letter)
        except OSError:
            _logger.debug("Volume illisible ignoré : %s", letter, exc_info=True)
            continue
        volumes.append(
            VolumeInfo(
                letter=letter,
                label=label or letter,
                filesystem=filesystem or partition.fstype,
                volume_type=_DRIVE_TYPE_MAP.get(drive_type_code, "unknown"),
                total_bytes=usage.total,
                used_bytes=usage.used,
                free_bytes=usage.free,
            )
        )
    return volumes


def send_to_recycle_bin(paths: Sequence[Path]) -> list[DeletionOutcome]:
    """Envoie chaque fichier à la Corbeille séparément (rapport partiel fiable par fichier)."""
    outcomes: list[DeletionOutcome] = []
    for path in paths:
        flags = shellcon.FOF_ALLOWUNDO | shellcon.FOF_NOCONFIRMATION | shellcon.FOF_SILENT
        operation = (0, shellcon.FO_DELETE, str(path), None, flags, None, None)
        try:
            # Le stub attend un SHFILEOPSTRUCT typé ; l'API réelle accepte un tuple brut
            # (vérifié manuellement) — limitation connue des stubs pywin32.
            result_code, _aborted = shell.SHFileOperation(operation)  # type: ignore[arg-type]
        except pywintypes.error as exc:
            outcomes.append(DeletionOutcome(str(path), False, str(exc)))
            continue
        if result_code == 0:
            outcomes.append(DeletionOutcome(str(path), True, None))
        else:
            outcomes.append(
                DeletionOutcome(str(path), False, f"Code d'erreur Windows {result_code}")
            )
    return outcomes


def reveal_in_explorer(path: Path) -> bool:
    explorer = Path(os.environ.get("WINDIR", r"C:\Windows")) / "explorer.exe"
    try:
        subprocess.run([str(explorer), "/select,", str(path)], check=False, shell=False)
    except OSError:
        _logger.exception("Impossible d'ouvrir l'Explorateur pour %s.", path)
        return False
    return True


def open_storage_sense() -> bool:
    """Lance l'outil officiel Windows plutôt que de réimplémenter un nettoyage système."""
    explorer = Path(os.environ.get("WINDIR", r"C:\Windows")) / "explorer.exe"
    try:
        subprocess.run([str(explorer), "ms-settings:storagesense"], check=False, shell=False)
    except OSError:
        _logger.exception("Impossible d'ouvrir l'Assistant Stockage.")
        return False
    return True
