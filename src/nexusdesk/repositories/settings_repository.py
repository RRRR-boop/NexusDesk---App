"""Dépôt des paramètres applicatifs (clé/valeur plat, cf. ADR-0003)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from nexusdesk.config.schema import AppSettings
from nexusdesk.database.session import session_scope
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.models.settings import SettingRow


class SettingsRepository:
    """Lecture/écriture des paramètres ; toute écriture passe par la file unique."""

    def __init__(self, session_factory: sessionmaker[Session], write_queue: WriteQueue) -> None:
        self._session_factory = session_factory
        self._write_queue = write_queue

    def get_all(self) -> AppSettings:
        with session_scope(self._session_factory) as session:
            rows = session.execute(select(SettingRow)).scalars().all()
            flat: dict[str, Any] = {row.key: json.loads(row.value) for row in rows}
        return AppSettings.model_validate(_unflatten(flat))

    def set(self, key: str, value: Any) -> None:
        self._write_queue.submit_write(lambda session: self._upsert(session, key, value)).result()

    def reset_to_defaults(self) -> AppSettings:
        defaults = AppSettings()
        for key, value in _flatten(defaults.model_dump()).items():
            self.set(key, value)
        return defaults

    @staticmethod
    def _upsert(session: Session, key: str, value: Any) -> None:
        row = session.get(SettingRow, key)
        payload = json.dumps(value)
        if row is None:
            session.add(SettingRow(key=key, value=payload, updated_at=datetime.now()))
        else:
            row.value = payload
            row.updated_at = datetime.now()


def _flatten(data: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping):
            result.update(_flatten(value, full_key))
        else:
            result[full_key] = value
    return result


def _unflatten(flat: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for dotted_key, value in flat.items():
        parts = dotted_key.split(".")
        cursor = result
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
    return result
