"""Fenêtre principale : navigation, raccourcis Ctrl+1..7, réduction dans le tray (ADR-0006)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from nexusdesk.config.schema import CloseBehavior
from nexusdesk.ui.shell.navigation import NavigationSidebar
from nexusdesk.viewmodels.shell_viewmodel import PAGE_IDS, ShellViewModel


class MainWindow(QMainWindow):
    minimized_to_tray = Signal()

    def __init__(self, shell_viewmodel: ShellViewModel, icon_color: str) -> None:
        super().__init__()
        self.setWindowTitle("NexusDesk")
        self.resize(1200, 800)

        self._shell_viewmodel = shell_viewmodel
        self._close_behavior: CloseBehavior = "minimize"
        self._first_minimize_notified = False
        self._page_indices: dict[str, int] = {}

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = NavigationSidebar(icon_color)
        self._sidebar.navigate_requested.connect(shell_viewmodel.navigate_to)
        self._sidebar.collapse_toggled.connect(shell_viewmodel.set_sidebar_collapsed)
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack, stretch=1)

        self.setCentralWidget(central)

        shell_viewmodel.page_changed.connect(self._on_page_changed)
        self._install_shortcuts()

    def register_page(self, page_id: str, widget: QWidget) -> None:
        index = self._stack.addWidget(widget)
        self._page_indices[page_id] = index

    def show_initial_page(self) -> None:
        self._sidebar.set_collapsed(self._shell_viewmodel.sidebar_collapsed)
        self._on_page_changed(self._shell_viewmodel.current_page)

    def set_close_behavior(self, behavior: CloseBehavior) -> None:
        self._close_behavior = behavior

    def _install_shortcuts(self) -> None:
        for index, page_id in enumerate(PAGE_IDS, start=1):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{index}"), self)
            shortcut.activated.connect(lambda pid=page_id: self._shell_viewmodel.navigate_to(pid))

    def _on_page_changed(self, page_id: str) -> None:
        index = self._page_indices.get(page_id)
        if index is not None:
            self._stack.setCurrentIndex(index)
        self._sidebar.select_page(page_id)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - signature imposée par Qt
        if self._close_behavior == "quit":
            event.accept()
            return
        event.ignore()
        self.hide()
        if not self._first_minimize_notified:
            self._first_minimize_notified = True
            self.minimized_to_tray.emit()
