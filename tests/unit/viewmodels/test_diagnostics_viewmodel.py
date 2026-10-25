from __future__ import annotations

from typing import Any

from nexusdesk.core.diagnostics import DiagnosticResult, FunctionDiagnosticCheck
from nexusdesk.core.tasks import TaskManager
from nexusdesk.viewmodels.diagnostics_viewmodel import DiagnosticsViewModel


def test_run_diagnostics_emits_results_ready(qtbot: Any) -> None:
    checks = [
        FunctionDiagnosticCheck(
            "ok-check", lambda: DiagnosticResult("ok-check", "ok", "tout va bien")
        )
    ]
    viewmodel = DiagnosticsViewModel(checks, TaskManager())

    results: list[list[DiagnosticResult]] = []
    viewmodel.results_ready.connect(results.append)
    viewmodel.run_diagnostics()

    with qtbot.waitSignal(viewmodel.results_ready, timeout=2000):
        pass

    assert len(results) == 1
    assert results[0][0].name == "ok-check"
    assert results[0][0].status == "ok"


def test_failing_check_becomes_an_error_result_not_a_crash(qtbot: Any) -> None:
    def _boom() -> DiagnosticResult:
        raise RuntimeError("échec de contrôle")

    checks = [FunctionDiagnosticCheck("boom-check", _boom)]
    viewmodel = DiagnosticsViewModel(checks, TaskManager())

    results: list[list[DiagnosticResult]] = []
    viewmodel.results_ready.connect(results.append)
    viewmodel.run_diagnostics()

    with qtbot.waitSignal(viewmodel.results_ready, timeout=2000):
        pass

    assert results[0][0].status == "error"
