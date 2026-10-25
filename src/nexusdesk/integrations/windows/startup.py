"""Lancement au démarrage de Windows via ``HKCU\\...\\Run`` (section 7, réversible).

Le chemin de l'exécutable écrit diffère entre le mode développeur (``python.exe`` via
``uv run``) et le mode packagé (``NexusDesk.exe``) : il est donc résolu dynamiquement au
moment de l'activation plutôt que mémorisé.
"""

from __future__ import annotations

import contextlib
import sys
import winreg

_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "NexusDesk"


def _executable_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{sys.argv[0]}"'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except FileNotFoundError:
        return False


def set_enabled(enabled: bool) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH) as key:
        if enabled:
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _executable_command())
        else:
            with contextlib.suppress(FileNotFoundError):
                winreg.DeleteValue(key, _VALUE_NAME)
