from __future__ import annotations

from typing import Any

from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from nexusdesk.config.schema import AppSettings
from nexusdesk.ui.shell.main_window import MainWindow
from nexusdesk.viewmodels.shell_viewmodel import PAGE_IDS, ShellViewModel


class _FakeSettingsRepository:
    def get_all(self) -> AppSettings:
        return AppSettings()

    def get_raw(self, _key: str, default: Any = None) -> Any:
        return default

    def set(self, _key: str, _value: Any) -> None:
        pass


def _build_window(qtbot: Any) -> tuple[MainWindow, ShellViewModel]:
    shell_viewmodel = ShellViewModel(_FakeSettingsRepository())  # type: ignore[arg-type]
    window = MainWindow(shell_viewmodel, "#000000")
    for page_id in (*PAGE_IDS, "settings", "diagnostics"):
        window.register_page(page_id, QLabel(page_id))
    window.show_initial_page()
    qtbot.addWidget(window)
    return window, shell_viewmodel


def test_ctrl_shortcuts_navigate_to_each_page(qtbot: Any) -> None:
    window, shell_viewmodel = _build_window(qtbot)
    window.show()
    qtbot.waitExposed(window)
    window.activateWindow()
    QTest.qWaitForWindowActive(window)

    for index, page_id in enumerate(PAGE_IDS, start=1):
        QTest.keySequence(window, QKeySequence(f"Ctrl+{index}"))
        assert shell_viewmodel.current_page == page_id


def test_close_minimizes_and_notifies_only_once(qtbot: Any) -> None:
    window, _ = _build_window(qtbot)
    window.show()

    notifications: list[int] = []
    window.minimized_to_tray.connect(lambda: notifications.append(1))

    window.close()
    assert window.isHidden()
    assert len(notifications) == 1

    window.show()
    window.close()
    assert len(notifications) == 1  # bandeau affiché une seule fois (section 6)


def test_close_quits_without_notification_when_configured(qtbot: Any) -> None:
    window, _ = _build_window(qtbot)
    window.set_close_behavior("quit")
    window.show()

    notifications: list[int] = []
    window.minimized_to_tray.connect(lambda: notifications.append(1))

    window.close()
    assert len(notifications) == 0
