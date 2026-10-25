from __future__ import annotations

from typing import Any

from nexusdesk.integrations.windows import startup


class _FakeKey:
    def __enter__(self) -> _FakeKey:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


def test_set_enabled_round_trip(monkeypatch: Any) -> None:
    store: dict[str, str] = {}

    def _fake_create_key(_hive: int, _path: str) -> _FakeKey:
        return _FakeKey()

    def _fake_open_key(_hive: int, _path: str) -> _FakeKey:
        return _FakeKey()

    def _fake_set_value(
        _key: _FakeKey, name: str, _reserved: int, _value_type: int, value: str
    ) -> None:
        store[name] = value

    def _fake_query_value(_key: _FakeKey, name: str) -> tuple[str, int]:
        if name not in store:
            raise FileNotFoundError(name)
        return (store[name], 1)

    def _fake_delete_value(_key: _FakeKey, name: str) -> None:
        store.pop(name, None)

    monkeypatch.setattr(startup.winreg, "CreateKeyEx", _fake_create_key)
    monkeypatch.setattr(startup.winreg, "OpenKey", _fake_open_key)
    monkeypatch.setattr(startup.winreg, "SetValueEx", _fake_set_value)
    monkeypatch.setattr(startup.winreg, "QueryValueEx", _fake_query_value)
    monkeypatch.setattr(startup.winreg, "DeleteValue", _fake_delete_value)

    assert startup.is_enabled() is False

    startup.set_enabled(True)
    assert startup.is_enabled() is True
    assert "NexusDesk" in store

    startup.set_enabled(False)
    assert startup.is_enabled() is False
    assert "NexusDesk" not in store
