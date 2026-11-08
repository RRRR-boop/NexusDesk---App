"""Garde-fous sur la configuration d'empaquetage (nexusdesk.spec, icône de l'exécutable).

L'exécutable empaqueté n'est pas construit par la suite de tests (trop long) : ces tests
vérifient au moins les deux réglages dont l'absence a cassé des préversions publiées.
"""

from __future__ import annotations

import ast
import struct
from pathlib import Path

from nexusdesk.ui.theme.icon_provider import APP_ICON_SIZES

_ROOT = Path(__file__).resolve().parents[2]
_ICO = _ROOT / "src" / "nexusdesk" / "resources" / "icons" / "app.ico"


def _spec_keyword(name: str) -> ast.expr:
    tree = ast.parse((_ROOT / "nexusdesk.spec").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == name:
            return node.value
    raise AssertionError(f"Argument {name}= absent de nexusdesk.spec")


def test_spec_bundles_win32timezone_imported_lazily_by_pywin32() -> None:
    # Sans lui, l'analyse d'un dossier contenant un lien physique échoue dans l'exécutable
    # (« No module named 'win32timezone' », préversions 0.2.1-beta.1 et beta.2).
    hidden_imports = ast.literal_eval(_spec_keyword("hiddenimports"))

    assert "win32timezone" in hidden_imports


def test_spec_sets_the_application_icon() -> None:
    assert "app.ico" in ast.unparse(_spec_keyword("icon"))


def test_app_ico_contains_every_size_up_to_256px() -> None:
    data = _ICO.read_bytes()
    reserved, kind, count = struct.unpack("<HHH", data[:6])
    sizes = []
    for index in range(count):
        width = data[6 + 16 * index]
        sizes.append(width or 256)  # 0 signifie 256 dans le format ICO

    assert (reserved, kind) == (0, 1)
    assert sorted(sizes) == sorted(APP_ICON_SIZES)
