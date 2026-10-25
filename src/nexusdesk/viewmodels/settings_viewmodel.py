"""Expose les paramètres Général/Apparence à l'interface sans dépendre de Qt Widgets."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from nexusdesk.config.schema import AppSettings
from nexusdesk.repositories.settings_repository import SettingsRepository


class SettingsViewModel(QObject):
    settings_changed = Signal(AppSettings)

    def __init__(self, settings_repository: SettingsRepository) -> None:
        super().__init__()
        self._settings_repository = settings_repository
        self._settings = settings_repository.get_all()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def save(self, settings: AppSettings) -> None:
        for key, value in settings.model_dump().items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    self._settings_repository.set(f"{key}.{sub_key}", sub_value)
            else:
                self._settings_repository.set(key, value)
        self._settings = settings
        self.settings_changed.emit(settings)

    def reset_to_defaults(self) -> None:
        self._settings = self._settings_repository.reset_to_defaults()
        self.settings_changed.emit(self._settings)
