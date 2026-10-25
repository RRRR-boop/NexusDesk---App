"""Barre de navigation latérale, repliable (icônes seules / icônes + libellés, section 5)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from nexusdesk.ui.theme.icon_provider import load_icon

_NAV_ITEMS = (
    ("dashboard", "Tableau de bord", "dashboard"),
    ("app_manager", "AppManager", "app_manager"),
    ("netwatch", "NetWatch", "netwatch"),
    ("screentext", "ScreenText", "screentext"),
    ("logdoctor", "LogDoctor", "logdoctor"),
    ("diskpilot", "DiskPilot", "diskpilot"),
    ("clipvault", "ClipVault", "clipvault"),
)

_ICON_SIZE = 20
_COLLAPSED_WIDTH = 56
_EXPANDED_WIDTH = 220


class NavigationSidebar(QWidget):
    navigate_requested = Signal(str)
    collapse_toggled = Signal(bool)

    def __init__(self, icon_color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon_color = icon_color
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toggle_button = QPushButton()
        self._toggle_button.setFlat(True)
        self._toggle_button.clicked.connect(self._on_toggle_clicked)
        layout.addWidget(self._toggle_button)

        self._list = QListWidget()
        self._list.setObjectName("navigationList")
        self._list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._list, stretch=1)

        self._settings_button = QPushButton("Paramètres")
        self._settings_button.setFlat(True)
        self._settings_button.clicked.connect(lambda: self.navigate_requested.emit("settings"))
        layout.addWidget(self._settings_button)

        self._diagnostics_button = QPushButton("Diagnostic")
        self._diagnostics_button.setFlat(True)
        self._diagnostics_button.clicked.connect(
            lambda: self.navigate_requested.emit("diagnostics")
        )
        layout.addWidget(self._diagnostics_button)

        self._populate_items()
        self._apply_collapsed_state()

    def _populate_items(self) -> None:
        for _page_id, label, icon_name in _NAV_ITEMS:
            item = QListWidgetItem(load_icon(icon_name, self._icon_color, _ICON_SIZE), label)
            item.setData(Qt.ItemDataRole.UserRole, _page_id)
            self._list.addItem(item)

    def _on_row_changed(self, row: int) -> None:
        if row < 0:
            return
        item = self._list.item(row)
        self.navigate_requested.emit(item.data(Qt.ItemDataRole.UserRole))

    def select_page(self, page_id: str) -> None:
        for row in range(self._list.count()):
            if self._list.item(row).data(Qt.ItemDataRole.UserRole) == page_id:
                self._list.setCurrentRow(row)
                return
        self._list.setCurrentRow(-1)

    def set_collapsed(self, collapsed: bool) -> None:
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self._apply_collapsed_state()

    def _apply_collapsed_state(self) -> None:
        self.setFixedWidth(_COLLAPSED_WIDTH if self._collapsed else _EXPANDED_WIDTH)
        icon_name = "chevron_right" if self._collapsed else "chevron_left"
        self._toggle_button.setIcon(load_icon(icon_name, self._icon_color, _ICON_SIZE))
        for row, (_page_id, label, _icon_name) in enumerate(_NAV_ITEMS):
            self._list.item(row).setText("" if self._collapsed else label)
        self._settings_button.setText("" if self._collapsed else "Paramètres")
        self._diagnostics_button.setText("" if self._collapsed else "Diagnostic")

    def _on_toggle_clicked(self) -> None:
        self.set_collapsed(not self._collapsed)
        self.collapse_toggled.emit(self._collapsed)
