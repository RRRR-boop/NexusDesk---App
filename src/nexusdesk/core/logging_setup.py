"""Configuration de la journalisation et gestionnaire global d'exceptions.

Deux garanties sont assurées ici : (1) aucune donnée personnelle (le chemin du profil
utilisateur) n'apparaît dans les journaux techniques, et (2) une exception non interceptée
ne doit jamais faire disparaître l'application sans explication ni trace.
"""

from __future__ import annotations

import logging
import logging.handlers
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path
from types import TracebackType

_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 4  # fichier courant + 4 sauvegardes = 5 fichiers au total
_USERPROFILE_PLACEHOLDER = "%USERPROFILE%"

_logger = logging.getLogger("nexusdesk")


def _redact(text: str) -> str:
    """Remplace le chemin du profil utilisateur par un espace réservé non personnel."""
    home = str(Path.home())
    redacted = text.replace(home, _USERPROFILE_PLACEHOLDER)
    redacted = redacted.replace(home.replace("\\", "/"), _USERPROFILE_PLACEHOLDER)
    return redacted


class _RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return _redact(super().format(record))


def configure_logging(logs_dir: Path, *, dev_mode: bool) -> None:
    """Installe les handlers de journalisation (fichier tournant + console en mode dev)."""
    _logger.setLevel(logging.DEBUG if dev_mode else logging.INFO)
    _logger.handlers.clear()

    formatter = _RedactingFormatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "nexusdesk.log",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    if dev_mode:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)


def _write_crash_report(logs_dir: Path, traceback_text: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = logs_dir / f"crash-{timestamp}.log"
    header = (
        f"NexusDesk — rapport de plantage local\n"
        f"Date : {datetime.now().isoformat()}\n"
        f"Python : {platform.python_version()}\n"
        f"Système : {platform.system()} {platform.release()} ({platform.machine()})\n"
        f"Ce rapport ne contient aucune donnée personnelle et n'est jamais envoyé.\n"
        f"{'-' * 60}\n"
    )
    report_path.write_text(_redact(header + traceback_text), encoding="utf-8")
    return report_path


def install_global_excepthook(logs_dir: Path) -> None:
    """Journalise, écrit un rapport de plantage et affiche un message compréhensible."""

    def _handle(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        traceback_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _logger.critical("Exception non interceptée :\n%s", traceback_text)
        report_path = _write_crash_report(logs_dir, traceback_text)
        _show_crash_dialog(report_path)

    sys.excepthook = _handle


def _show_crash_dialog(report_path: Path) -> None:
    """Affiche une boîte de dialogue si une interface Qt est disponible, sinon reste muet."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
    except ImportError:
        return

    if QApplication.instance() is None:
        return

    QMessageBox.critical(
        None,
        "NexusDesk — erreur inattendue",
        "Une erreur inattendue s'est produite. L'application continue si possible.\n\n"
        f"Détails enregistrés localement dans :\n{report_path}",
    )
