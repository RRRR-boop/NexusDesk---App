from __future__ import annotations

from typing import Any

from nexusdesk.config.schema import AppSettings, DiskPilotSettings
from nexusdesk.ui.pages.settings_page import SettingsPage
from nexusdesk.viewmodels.settings_viewmodel import SettingsViewModel


class _FakeSettingsRepository:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self.stored: dict[str, Any] = {}

    def get_all(self) -> AppSettings:
        return self._settings

    def set(self, key: str, value: Any) -> None:
        self.stored[key] = value

    def reset_to_defaults(self) -> AppSettings:
        self._settings = AppSettings()
        return self._settings


def _build_page(qtbot: Any, settings: AppSettings) -> tuple[SettingsPage, _FakeSettingsRepository]:
    repository = _FakeSettingsRepository(settings)
    viewmodel = SettingsViewModel(repository)  # type: ignore[arg-type]
    page = SettingsPage(viewmodel)
    qtbot.addWidget(page)
    return page, repository


def test_changing_general_tab_keeps_diskpilot_settings_without_ui_controls(qtbot: Any) -> None:
    custom = DiskPilotSettings(
        extra_excluded_paths=["D:\\Archives"],
        min_duplicate_size_bytes=5 * 1024 * 1024,
        warning_free_percent=20.0,
        alert_free_percent=8.0,
    )
    page, repository = _build_page(qtbot, AppSettings(diskpilot=custom))

    page._developer_mode_checkbox.setChecked(True)

    assert repository.stored["general.developer_mode"] is True
    assert repository.stored["diskpilot.extra_excluded_paths"] == ["D:\\Archives"]
    assert repository.stored["diskpilot.min_duplicate_size_bytes"] == 5 * 1024 * 1024
    assert repository.stored["diskpilot.warning_free_percent"] == 20.0
    assert repository.stored["diskpilot.alert_free_percent"] == 8.0


def test_diskpilot_tab_saves_min_duplicate_size_in_bytes(qtbot: Any) -> None:
    page, repository = _build_page(qtbot, AppSettings())
    assert page._min_duplicate_size_spin.value() == 1.0  # 1 Mo par défaut (section 11)

    page._min_duplicate_size_spin.setValue(2.5)

    assert repository.stored["diskpilot.min_duplicate_size_bytes"] == round(2.5 * 1024 * 1024)


def test_alert_threshold_is_kept_strictly_below_warning_threshold(qtbot: Any) -> None:
    page, repository = _build_page(qtbot, AppSettings())

    page._alert_free_spin.setValue(30.0)  # au-dessus de l'avertissement par défaut (15 %)

    assert page._alert_free_spin.value() == 14.0
    assert repository.stored["diskpilot.alert_free_percent"] == 14.0
    assert repository.stored["diskpilot.warning_free_percent"] == 15.0


def test_exclusions_editor_saves_normalized_paths_without_duplicates(qtbot: Any) -> None:
    page, repository = _build_page(qtbot, AppSettings())

    page.add_exclusion("D:/Archives/Photos")
    page.add_exclusion(r"d:\archives\photos")  # même dossier, casse différente
    page.add_exclusion(r"relatif\dossier")  # refusé : chemin non absolu

    assert repository.stored["diskpilot.extra_excluded_paths"] == [r"D:\Archives\Photos"]

    page._exclusions_list.item(0).setSelected(True)
    page._remove_exclusion_button.click()

    assert repository.stored["diskpilot.extra_excluded_paths"] == []
