from __future__ import annotations

from typing import Any

from nexusdesk.config.schema import AppSettings, GeneralSettings
from nexusdesk.viewmodels.shell_viewmodel import ShellViewModel


class _FakeSettingsRepository:
    def __init__(self, home_page: str = "dashboard") -> None:
        self._settings = AppSettings(general=GeneralSettings(home_page=home_page))
        self._raw: dict[str, Any] = {}

    def get_all(self) -> AppSettings:
        return self._settings

    def get_raw(self, key: str, default: Any = None) -> Any:
        return self._raw.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._raw[key] = value


def test_initial_page_falls_back_to_dashboard_for_unknown_home_page() -> None:
    repository = _FakeSettingsRepository(home_page="unknown-page")
    viewmodel = ShellViewModel(repository)  # type: ignore[arg-type]
    assert viewmodel.current_page == "dashboard"


def test_navigate_to_emits_signal_only_on_real_change(qtbot: Any) -> None:
    repository = _FakeSettingsRepository()
    viewmodel = ShellViewModel(repository)  # type: ignore[arg-type]

    changes: list[str] = []
    viewmodel.page_changed.connect(changes.append)

    viewmodel.navigate_to("netwatch")
    viewmodel.navigate_to("netwatch")  # pas de changement : pas de nouveau signal
    viewmodel.navigate_to("diskpilot")

    assert changes == ["netwatch", "diskpilot"]


def test_set_sidebar_collapsed_persists_via_repository() -> None:
    repository = _FakeSettingsRepository()
    viewmodel = ShellViewModel(repository)  # type: ignore[arg-type]

    viewmodel.set_sidebar_collapsed(True)

    assert repository.get_raw("ui.sidebar_collapsed") is True
    assert viewmodel.sidebar_collapsed is True
