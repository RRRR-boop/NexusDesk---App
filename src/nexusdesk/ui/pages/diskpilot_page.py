from __future__ import annotations

from PySide6.QtWidgets import QWidget

from nexusdesk.ui.components.placeholder_page import PlaceholderPage


class DiskPilotPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("DiskPilot", "Lot 1", parent)
