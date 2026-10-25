"""Page générique « Module — à venir » (section 1 : pas de bouton sans fonction réelle).

Chaque page de module affiche honnêtement qu'elle n'est pas encore implémentée plutôt que
de présenter des contrôles inactifs ou des données factices.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title: str, lot_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setProperty("role", "pageTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        caption_label = QLabel(f"Module à venir — {lot_label}")
        caption_label.setProperty("role", "caption")
        caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(caption_label)
