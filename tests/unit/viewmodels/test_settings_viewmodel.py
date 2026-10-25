from __future__ import annotations

from typing import Any

from nexusdesk.config.schema import AppearanceSettings, AppSettings, GeneralSettings
from nexusdesk.viewmodels.settings_viewmodel import SettingsViewModel


class _FakeSettingsRepository:
    def __init__(self) -> None:
        self._settings = AppSettings()
        self.set_calls: list[tuple[str, Any]] = []

    def get_all(self) -> AppSettings:
        return self._settings

    def set(self, key: str, value: Any) -> None:
        self.set_calls.append((key, value))

    def reset_to_defaults(self) -> AppSettings:
        self._settings = AppSettings()
        return self._settings


def test_save_writes_every_flattened_field_and_emits_signal(qtbot: Any) -> None:
    repository = _FakeSettingsRepository()
    viewmodel = SettingsViewModel(repository)  # type: ignore[arg-type]

    received: list[AppSettings] = []
    viewmodel.settings_changed.connect(received.append)

    new_settings = AppSettings(
        general=GeneralSettings(close_behavior="quit"),
        appearance=AppearanceSettings(theme="light"),
    )
    viewmodel.save(new_settings)

    assert viewmodel.settings.appearance.theme == "light"
    assert received == [new_settings]
    assert ("general.close_behavior", "quit") in repository.set_calls
    assert ("appearance.theme", "light") in repository.set_calls


def test_reset_to_defaults_delegates_to_repository_and_emits_signal(qtbot: Any) -> None:
    repository = _FakeSettingsRepository()
    viewmodel = SettingsViewModel(repository)  # type: ignore[arg-type]

    received: list[AppSettings] = []
    viewmodel.settings_changed.connect(received.append)

    viewmodel.reset_to_defaults()

    assert len(received) == 1
    assert viewmodel.settings.appearance.theme == "dark"
