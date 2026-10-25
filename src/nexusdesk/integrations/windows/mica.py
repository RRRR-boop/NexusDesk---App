"""Effet Mica (fond translucide Windows 11) via DwmSetWindowAttribute.

``DWMWA_SYSTEMBACKDROP_TYPE`` n'existe qu'à partir de Windows 11 22H2 (build 22621) ; en
dessous, ou si l'appel échoue (DWM composite désactivé, machine virtuelle...), on se replie
silencieusement sur la couleur de fond unie (``bg.base``), jamais d'exception visible.
"""

from __future__ import annotations

import ctypes
import logging
import sys

_logger = logging.getLogger("nexusdesk.integrations.mica")

_DWMWA_SYSTEMBACKDROP_TYPE = 38
_DWMSBT_NONE = 1
_DWMSBT_MAINWINDOW = 2  # Mica
_MIN_BUILD_FOR_MICA = 22621


def _windows_build() -> int:
    try:
        return int(sys.getwindowsversion().build)
    except AttributeError:
        return 0


def is_mica_supported() -> bool:
    return sys.platform == "win32" and _windows_build() >= _MIN_BUILD_FOR_MICA


def apply_mica(hwnd: int, enabled: bool) -> bool:
    """Tente d'activer/désactiver Mica sur la fenêtre ``hwnd``. Renvoie le succès réel."""
    if not is_mica_supported():
        return False

    backdrop_type = _DWMSBT_MAINWINDOW if enabled else _DWMSBT_NONE
    value = ctypes.c_int(backdrop_type)
    try:
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_int(_DWMWA_SYSTEMBACKDROP_TYPE),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except OSError:
        _logger.debug("DwmSetWindowAttribute indisponible ; repli sur bg.base.", exc_info=True)
        return False
    return bool(result == 0)
