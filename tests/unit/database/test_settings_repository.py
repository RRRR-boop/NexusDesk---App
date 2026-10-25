from __future__ import annotations

from pathlib import Path

from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.migration_runner import ensure_up_to_date
from nexusdesk.database.session import make_session_factory
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.repositories.settings_repository import SettingsRepository


def _build_repository(tmp_path: Path) -> SettingsRepository:
    db_path = tmp_path / "nexusdesk.db"
    engine = create_sqlite_engine(db_path)
    ensure_up_to_date(engine, db_path, tmp_path / "backups")
    session_factory = make_session_factory(engine)
    write_queue = WriteQueue(session_factory)
    return SettingsRepository(session_factory, write_queue)


def test_get_all_returns_defaults_when_empty(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)
    settings = repository.get_all()

    assert settings.general.close_behavior == "minimize"
    assert settings.appearance.theme == "dark"


def test_set_and_get_all_round_trip(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)

    repository.set("general.close_behavior", "quit")
    repository.set("appearance.theme", "light")

    settings = repository.get_all()
    assert settings.general.close_behavior == "quit"
    assert settings.appearance.theme == "light"


def test_free_form_key_does_not_break_get_all(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)

    repository.set("ui.sidebar_collapsed", True)

    assert repository.get_raw("ui.sidebar_collapsed") is True
    assert repository.get_raw("ui.unknown_key", default="fallback") == "fallback"
    # Une clé hors schéma ne doit jamais faire échouer la reconstruction d'AppSettings
    # (ADR-0003 : extra="ignore" au niveau racine).
    settings = repository.get_all()
    assert settings.general.close_behavior == "minimize"


def test_reset_to_defaults(tmp_path: Path) -> None:
    repository = _build_repository(tmp_path)
    repository.set("appearance.theme", "light")

    defaults = repository.reset_to_defaults()

    assert defaults.appearance.theme == "dark"
    assert repository.get_all().appearance.theme == "dark"
