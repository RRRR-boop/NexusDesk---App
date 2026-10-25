"""Registre extensible de contrôles de diagnostic (section 15).

Ce module ne connaît aucun contrôle concret : il définit seulement la forme d'un contrôle
et l'exécution de la liste. Les contrôles réels (version Windows, droits d'écriture,
intégrité des bases...) sont construits par la racine de composition (``app.py``), qui est
seule autorisée à importer à la fois ``database/`` et ``core/`` ; les lots suivants
ajouteront leurs propres contrôles (WinGet, Tesseract, langues OCR) sans toucher à ce
registre ni à la page qui l'affiche.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

DiagnosticStatus = Literal["ok", "warning", "error", "info"]


@dataclass(frozen=True)
class DiagnosticResult:
    name: str
    status: DiagnosticStatus
    detail: str


class DiagnosticCheck(Protocol):
    name: str

    def run(self) -> DiagnosticResult: ...


@dataclass(frozen=True)
class FunctionDiagnosticCheck:
    """Adapte une simple fonction en ``DiagnosticCheck`` sans imposer une sous-classe."""

    name: str
    run_fn: Callable[[], DiagnosticResult]

    def run(self) -> DiagnosticResult:
        return self.run_fn()


def run_all(checks: list[DiagnosticCheck]) -> list[DiagnosticResult]:
    results: list[DiagnosticResult] = []
    for check in checks:
        try:
            results.append(check.run())
        except Exception as exc:  # noqa: BLE001 - un contrôle qui plante devient un résultat "error"
            results.append(DiagnosticResult(name=check.name, status="error", detail=str(exc)))
    return results
