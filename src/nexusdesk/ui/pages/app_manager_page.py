from __future__ import annotations

from PySide6.QtWidgets import QWidget

from nexusdesk.ui.components.placeholder_page import PlaceholderPage


class AppManagerPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("AppManager", "Lot 7", parent)
