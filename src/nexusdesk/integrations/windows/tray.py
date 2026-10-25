"""Icône de zone de notification (section 6) : menu Ouvrir / Paramètres / Quitter."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent: QWidget | None = None) -> None:
        super().__init__(icon, parent)
        self._menu = QMenu()
        self.open_action = self._menu.addAction("Ouvrir")
        self.settings_action = self._menu.addAction("Paramètres")
        self._menu.addSeparator()
        self.quit_action = self._menu.addAction("Quitter")
        self.setContextMenu(self._menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_action.trigger()
