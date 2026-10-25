"""Notifications natives via l'icône de zone de notification (section 6).

``QSystemTrayIcon.showMessage`` produit nativement une notification du Centre de
notifications Windows ; au lot 0, aucun module métier n'a encore besoin d'une API Toast XML
dédiée.
"""

from __future__ import annotations

from PySide6.QtWidgets import QSystemTrayIcon


def show_notification(
    tray: QSystemTrayIcon, title: str, message: str, *, critical: bool = False
) -> None:
    icon = (
        QSystemTrayIcon.MessageIcon.Critical
        if critical
        else QSystemTrayIcon.MessageIcon.Information
    )
    tray.showMessage(title, message, icon)
