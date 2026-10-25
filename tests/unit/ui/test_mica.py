from __future__ import annotations

from typing import Any

from nexusdesk.integrations.windows import mica


def test_apply_mica_returns_false_when_unsupported(monkeypatch: Any) -> None:
    monkeypatch.setattr(mica, "is_mica_supported", lambda: False)
    assert mica.apply_mica(12345, True) is False


def test_apply_mica_falls_back_silently_on_oserror(monkeypatch: Any) -> None:
    monkeypatch.setattr(mica, "is_mica_supported", lambda: True)

    class _FakeDwmApi:
        def DwmSetWindowAttribute(self, *args: object, **kwargs: object) -> int:  # noqa: N802
            raise OSError("DWM indisponible (machine virtuelle, composition désactivée...)")

    class _FakeWindll:
        dwmapi = _FakeDwmApi()

    monkeypatch.setattr(mica.ctypes, "windll", _FakeWindll())

    # Ne doit jamais lever : repli silencieux sur bg.base (section 5).
    assert mica.apply_mica(12345, True) is False
