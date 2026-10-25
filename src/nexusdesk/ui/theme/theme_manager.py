"""Pilotage du thème actif (section 5) : QSS, Mica et mode « Suivre Windows ».

``ui/`` ne doit jamais importer ``integrations/`` (règle de couches, section 4) : la
fonction qui applique réellement Mica est injectée par la racine de composition
(``app.py``) plutôt qu'importée ici directement.
"""

from __future__ import annotations

import winreg
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from nexusdesk.config.schema import AppearanceSettings
from nexusdesk.ui.theme.qss_builder import build_qss
from nexusdesk.ui.theme.tokens import ThemeName, colors_for

MicaApplier = Callable[[int, bool], bool]


def _windows_prefers_light() -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return bool(value)
    except OSError:
        return False


class ThemeManager(QObject):
    theme_changed = Signal(str)

    def __init__(self, app: QApplication, mica_applier: MicaApplier) -> None:
        super().__init__()
        self._app = app
        self._mica_applier = mica_applier
        self._mica_hwnds: list[int] = []

    def resolve_theme(self, appearance: AppearanceSettings) -> ThemeName:
        if appearance.theme == "system":
            return "light" if _windows_prefers_light() else "dark"
        return appearance.theme

    def apply(self, appearance: AppearanceSettings) -> None:
        resolved = self.resolve_theme(appearance)
        colors = colors_for(resolved)
        qss = build_qss(colors, appearance.density, appearance.text_size)
        self._app.setStyleSheet(qss)
        for hwnd in self._mica_hwnds:
            self._mica_applier(hwnd, appearance.mica_enabled)
        self.theme_changed.emit(resolved)

    def register_mica_window(self, hwnd: int) -> None:
        self._mica_hwnds.append(hwnd)
