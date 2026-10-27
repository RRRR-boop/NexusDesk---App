"""Racine de composition : assemble toutes les couches.

Seul module autorisé à importer à la fois ``ui/``, ``viewmodels/``, ``services/``,
``repositories/``, ``database/`` et ``integrations/`` (section 4) — il n'est donc soumis à
aucun des contrats de couches vérifiés par import-linter.
"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nexusdesk.config.schema import AppSettings
from nexusdesk.core import paths
from nexusdesk.core.diagnostics import DiagnosticCheck, DiagnosticResult, FunctionDiagnosticCheck
from nexusdesk.core.logging_setup import configure_logging, install_global_excepthook
from nexusdesk.core.tasks import TaskManager
from nexusdesk.database.backup import check_integrity
from nexusdesk.database.engine import create_sqlite_engine
from nexusdesk.database.migration_runner import ensure_up_to_date
from nexusdesk.database.session import make_session_factory
from nexusdesk.database.write_queue import WriteQueue
from nexusdesk.integrations.windows import filesystem as diskpilot_filesystem
from nexusdesk.integrations.windows.mica import apply_mica
from nexusdesk.integrations.windows.notifications import show_notification
from nexusdesk.integrations.windows.single_instance import (
    OPEN_MAIN_WINDOW,
    QUIT,
    CommandServer,
)
from nexusdesk.integrations.windows.startup import set_enabled as set_startup_enabled
from nexusdesk.integrations.windows.tray import TrayIcon
from nexusdesk.models.diskpilot_cache import CacheBase
from nexusdesk.repositories.diskpilot_duplicate_repository import (
    DiskPilotDuplicateRepository,
)
from nexusdesk.repositories.diskpilot_hash_cache_repository import (
    DiskPilotHashCacheRepository,
)
from nexusdesk.repositories.diskpilot_scan_repository import DiskPilotScanRepository
from nexusdesk.repositories.settings_repository import SettingsRepository
from nexusdesk.ui.pages.app_manager_page import AppManagerPage
from nexusdesk.ui.pages.clipvault_page import ClipVaultPage
from nexusdesk.ui.pages.dashboard_page import DashboardPage
from nexusdesk.ui.pages.diagnostics_page import DiagnosticsPage
from nexusdesk.ui.pages.diskpilot import DiskPilotPage
from nexusdesk.ui.pages.logdoctor_page import LogDoctorPage
from nexusdesk.ui.pages.netwatch_page import NetWatchPage
from nexusdesk.ui.pages.screentext_page import ScreenTextPage
from nexusdesk.ui.pages.settings_page import SettingsPage
from nexusdesk.ui.shell.main_window import MainWindow
from nexusdesk.ui.theme.icon_provider import load_icon
from nexusdesk.ui.theme.theme_manager import ThemeManager
from nexusdesk.ui.theme.tokens import colors_for
from nexusdesk.viewmodels.diagnostics_viewmodel import DiagnosticsViewModel
from nexusdesk.viewmodels.diskpilot_cleanup_viewmodel import CleanupSuggestionsViewModel
from nexusdesk.viewmodels.diskpilot_deletion_viewmodel import DeletionViewModel
from nexusdesk.viewmodels.diskpilot_duplicates_viewmodel import DuplicatesViewModel
from nexusdesk.viewmodels.diskpilot_history_viewmodel import ScanHistoryViewModel
from nexusdesk.viewmodels.diskpilot_scan_viewmodel import ScanViewModel
from nexusdesk.viewmodels.diskpilot_viewmodel import DiskPilotViewModel
from nexusdesk.viewmodels.diskpilot_volumes_viewmodel import VolumesViewModel
from nexusdesk.viewmodels.settings_viewmodel import SettingsViewModel
from nexusdesk.viewmodels.shell_viewmodel import ShellViewModel

_logger = logging.getLogger("nexusdesk.app")

_IPC_QUIT_ENV_VAR = "NEXUSDESK_ALLOW_IPC_QUIT"  # ADR-0009 : réservé à scripts/smoke-test.ps1


class Application:
    def __init__(self, qt_app: QApplication, *, dev_mode: bool) -> None:
        self._qt_app = qt_app

        self.data_dir = paths.get_data_dir()
        self.backups_dir = paths.get_backups_dir()
        self.logs_dir = paths.get_logs_dir()

        configure_logging(self.logs_dir, dev_mode=dev_mode)
        install_global_excepthook(self.logs_dir)

        nexusdesk_db_path = self.data_dir / "nexusdesk.db"
        metrics_db_path = self.data_dir / "metrics.db"

        self._nexusdesk_engine = create_sqlite_engine(nexusdesk_db_path)
        self._metrics_engine = create_sqlite_engine(metrics_db_path)
        with self._metrics_engine.connect():
            pass  # crée metrics.db et applique les PRAGMA (ADR-0008) ; pas encore de schéma

        migration_result = ensure_up_to_date(
            self._nexusdesk_engine, nexusdesk_db_path, self.backups_dir
        )
        _logger.info(migration_result.message)
        self.read_only = migration_result.read_only

        session_factory = make_session_factory(self._nexusdesk_engine)
        self._write_queue = WriteQueue(session_factory)
        self.settings_repository = SettingsRepository(session_factory, self._write_queue)

        diskpilot_cache_db_path = paths.get_cache_dir() / "diskpilot_hash_cache.db"
        self._diskpilot_cache_engine = create_sqlite_engine(diskpilot_cache_db_path)
        CacheBase.metadata.create_all(self._diskpilot_cache_engine)  # ADR-0015 : hors Alembic
        diskpilot_cache_session_factory = make_session_factory(self._diskpilot_cache_engine)
        self._diskpilot_cache_write_queue = WriteQueue(diskpilot_cache_session_factory)

        diskpilot_scan_repository = DiskPilotScanRepository(session_factory, self._write_queue)
        diskpilot_scan_repository.mark_stale_running_as_failed()
        diskpilot_duplicate_repository = DiskPilotDuplicateRepository(
            session_factory, self._write_queue
        )
        diskpilot_hash_cache_repository = DiskPilotHashCacheRepository(
            diskpilot_cache_session_factory, self._diskpilot_cache_write_queue
        )

        self.task_manager = TaskManager()
        self.theme_manager = ThemeManager(qt_app, mica_applier=apply_mica)

        self.shell_viewmodel = ShellViewModel(self.settings_repository)
        self.settings_viewmodel = SettingsViewModel(self.settings_repository)
        self.settings_viewmodel.settings_changed.connect(self._on_settings_changed)

        checks = self._build_diagnostic_checks(nexusdesk_db_path, metrics_db_path)
        self.diagnostics_viewmodel = DiagnosticsViewModel(checks, self.task_manager)

        self.diskpilot_viewmodel = DiskPilotViewModel(
            volumes=VolumesViewModel(
                diskpilot_filesystem.list_volumes, self.settings_repository, self.task_manager
            ),
            scan=ScanViewModel(
                diskpilot_filesystem.get_size_on_disk,
                diskpilot_filesystem.get_hardlink_key,
                diskpilot_scan_repository,
                self.task_manager,
            ),
            duplicates=DuplicatesViewModel(
                diskpilot_hash_cache_repository, diskpilot_duplicate_repository, self.task_manager
            ),
            deletion=DeletionViewModel(diskpilot_filesystem.send_to_recycle_bin, self.task_manager),
            cleanup=CleanupSuggestionsViewModel(
                diskpilot_filesystem.open_storage_sense, self.task_manager
            ),
            history=ScanHistoryViewModel(diskpilot_scan_repository, self.task_manager),
        )

        appearance = self.settings_viewmodel.settings.appearance
        colors = colors_for(self.theme_manager.resolve_theme(appearance))
        icon_color = colors.text_primary

        self.main_window = MainWindow(self.shell_viewmodel, icon_color)
        self.main_window.register_page("dashboard", DashboardPage())
        self.main_window.register_page("app_manager", AppManagerPage())
        self.main_window.register_page("netwatch", NetWatchPage())
        self.main_window.register_page("screentext", ScreenTextPage())
        self.main_window.register_page("logdoctor", LogDoctorPage())
        self.diskpilot_page = DiskPilotPage(
            self.diskpilot_viewmodel,
            diskpilot_filesystem.reveal_in_explorer,
            self.settings_viewmodel.settings.diskpilot.min_duplicate_size_bytes,
        )
        self.main_window.register_page("diskpilot", self.diskpilot_page)
        self.main_window.register_page("clipvault", ClipVaultPage())
        self.main_window.register_page("settings", SettingsPage(self.settings_viewmodel))
        self.main_window.register_page("diagnostics", DiagnosticsPage(self.diagnostics_viewmodel))
        self.main_window.minimized_to_tray.connect(self._on_minimized_to_tray)

        self.theme_manager.register_mica_window(int(self.main_window.winId()))
        self.theme_manager.theme_changed.connect(self.diskpilot_page.set_theme)
        self.theme_manager.apply(appearance)
        self.main_window.set_close_behavior(self.settings_viewmodel.settings.general.close_behavior)

        self.tray_icon = TrayIcon(load_icon("app", icon_color, 32))
        self.tray_icon.setToolTip("NexusDesk")
        self.tray_icon.open_action.triggered.connect(self._show_main_window)
        self.tray_icon.settings_action.triggered.connect(self._open_settings)
        self.tray_icon.quit_action.triggered.connect(qt_app.quit)
        self.tray_icon.show()

        self.command_server = CommandServer()
        self.command_server.command_received.connect(self._on_command_received)
        self.command_server.start()

        qt_app.aboutToQuit.connect(self._shutdown)
        self.main_window.show_initial_page()

    def _build_diagnostic_checks(
        self, nexusdesk_db_path: Path, metrics_db_path: Path
    ) -> list[DiagnosticCheck]:
        def _check_windows_version() -> DiagnosticResult:
            if platform.system() != "Windows":
                return DiagnosticResult(
                    "Version de Windows", "warning", "Système non Windows détecté."
                )
            return DiagnosticResult(
                "Version de Windows", "ok", f"Windows {platform.release()} ({platform.version()})"
            )

        def _check_data_dir_writable() -> DiagnosticResult:
            probe = self.data_dir / ".nexusdesk_write_check"
            try:
                probe.write_text("ok", encoding="utf-8")
                probe.unlink()
            except OSError as exc:
                return DiagnosticResult("Droits d'écriture (données)", "error", str(exc))
            return DiagnosticResult("Droits d'écriture (données)", "ok", str(self.data_dir))

        def _check_db_integrity(name: str, db_path: Path) -> DiagnosticResult:
            if not db_path.exists():
                return DiagnosticResult(name, "info", "Base non encore créée.")
            ok = check_integrity(db_path)
            return DiagnosticResult(name, "ok" if ok else "error", "PRAGMA integrity_check")

        def _check_shortcuts() -> DiagnosticResult:
            return DiagnosticResult(
                "Raccourcis enregistrés",
                "info",
                "Aucun raccourci métier à vérifier pour l'instant.",
            )

        return [
            FunctionDiagnosticCheck("Version de Windows", _check_windows_version),
            FunctionDiagnosticCheck("Droits d'écriture (données)", _check_data_dir_writable),
            FunctionDiagnosticCheck(
                "Intégrité de nexusdesk.db",
                lambda: _check_db_integrity("Intégrité de nexusdesk.db", nexusdesk_db_path),
            ),
            FunctionDiagnosticCheck(
                "Intégrité de metrics.db",
                lambda: _check_db_integrity("Intégrité de metrics.db", metrics_db_path),
            ),
            FunctionDiagnosticCheck("Raccourcis enregistrés", _check_shortcuts),
        ]

    def _on_settings_changed(self, settings: AppSettings) -> None:
        self.theme_manager.apply(settings.appearance)
        self.main_window.set_close_behavior(settings.general.close_behavior)
        set_startup_enabled(settings.general.launch_at_startup)

    def _show_main_window(self) -> None:
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _open_settings(self) -> None:
        self.shell_viewmodel.navigate_to("settings")
        self._show_main_window()

    def _on_minimized_to_tray(self) -> None:
        show_notification(
            self.tray_icon,
            "NexusDesk",
            "NexusDesk continue de fonctionner dans la zone de notification.",
        )

    def _on_command_received(self, command: str) -> None:
        if command == OPEN_MAIN_WINDOW:
            self._show_main_window()
        elif command == QUIT and os.environ.get(_IPC_QUIT_ENV_VAR) == "1":
            self._qt_app.quit()

    def _shutdown(self) -> None:
        self.task_manager.cancel_all()
        self.task_manager.wait_for_done(3000)
        self._write_queue.stop(3.0)
        self._diskpilot_cache_write_queue.stop(3.0)
        self.command_server.stop(1.0)
        self._nexusdesk_engine.dispose()
        self._metrics_engine.dispose()
        self._diskpilot_cache_engine.dispose()
