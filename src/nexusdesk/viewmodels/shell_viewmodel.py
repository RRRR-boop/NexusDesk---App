"""État de navigation du shell (page active, repli de la barre latérale).

Zéro dépendance à Qt Widgets : seuls ``QObject``/``Signal`` (QtCore) sont utilisés, pour
rester testable sans interface et respecter la règle de couches (``viewmodels`` ne doit
jamais importer ``ui``).
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from nexusdesk.repositories.settings_repository import SettingsRepository

_SIDEBAR_COLLAPSED_KEY = "ui.sidebar_collapsed"

PAGE_IDS = (
    "dashboard",
    "app_manager",
    "netwatch",
    "screentext",
    "logdoctor",
    "diskpilot",
    "clipvault",
)


class ShellViewModel(QObject):
    page_changed = Signal(str)
    sidebar_collapsed_changed = Signal(bool)

    def __init__(self, settings_repository: SettingsRepository) -> None:
        super().__init__()
        self._settings_repository = settings_repository
        home_page = settings_repository.get_all().general.home_page
        self._current_page = home_page if home_page in PAGE_IDS else "dashboard"
        self._sidebar_collapsed = bool(
            settings_repository.get_raw(_SIDEBAR_COLLAPSED_KEY, default=False)
        )

    @property
    def current_page(self) -> str:
        return self._current_page

    @property
    def sidebar_collapsed(self) -> bool:
        return self._sidebar_collapsed

    def navigate_to(self, page_id: str) -> None:
        if page_id == self._current_page:
            return
        self._current_page = page_id
        self.page_changed.emit(page_id)

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        if collapsed == self._sidebar_collapsed:
            return
        self._sidebar_collapsed = collapsed
        self._settings_repository.set(_SIDEBAR_COLLAPSED_KEY, collapsed)
        self.sidebar_collapsed_changed.emit(collapsed)
