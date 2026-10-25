from __future__ import annotations

from PySide6.QtWidgets import QWidget

from nexusdesk.ui.components.placeholder_page import PlaceholderPage


class ScreenTextPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("ScreenText", "Lot 5", parent)
