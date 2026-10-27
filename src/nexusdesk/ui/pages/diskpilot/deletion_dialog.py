"""Boîte de dialogue de suppression DiskPilot (section 11) : revérification puis
confirmation explicite avant tout envoi à la Corbeille, rapport partiel après coup.

Modale (``exec()``) : bloque le reste de l'interface pendant la vérification/suppression,
ce qui sérialise naturellement l'usage du ``DeletionViewModel`` partagé entre panneaux sans
qu'aucun panneau n'ait à filtrer les signaux d'un autre.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from nexusdesk.models.diskpilot_domain import DeletionPreview, DeletionReport
from nexusdesk.ui.components.formatting import format_bytes
from nexusdesk.viewmodels.diskpilot_deletion_viewmodel import DeletionViewModel

_MAX_LISTED_FAILURES = 10


class DeletionDialog(QDialog):
    def __init__(
        self,
        viewmodel: DeletionViewModel,
        paths: list[Path],
        sizes: dict[Path, int],
        mtimes: dict[Path, float],
        scan_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Confirmer la suppression")
        self.setMinimumWidth(420)
        self._viewmodel = viewmodel
        self._sizes = sizes
        self._scan_root = scan_root
        self._preview: DeletionPreview | None = None
        self.result_report: DeletionReport | None = None

        self._message = QLabel("Vérification en cours…")
        self._message.setWordWrap(True)

        self._confirm_button = QPushButton("Envoyer à la Corbeille")
        self._confirm_button.setProperty("role", "primary")
        self._confirm_button.setEnabled(False)
        self._confirm_button.clicked.connect(self._on_confirm_clicked)

        self._close_button = QPushButton("Annuler")
        self._close_button.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self._close_button)
        buttons_layout.addWidget(self._confirm_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._message)
        layout.addLayout(buttons_layout)

        viewmodel.preview_ready.connect(self._on_preview_ready)
        viewmodel.deletion_finished.connect(self._on_deletion_finished)
        viewmodel.failed.connect(self._on_failed)

        viewmodel.request_preview(paths, sizes, mtimes)

    def _on_preview_ready(self, preview: object) -> None:
        if not isinstance(preview, DeletionPreview):
            return
        self._preview = preview
        lines = [
            f"{len(preview.valid_paths)} fichier(s) prêt(s) pour la Corbeille "
            f"({format_bytes(preview.total_size)})."
        ]
        if preview.changed_paths:
            lines.append(
                f"{len(preview.changed_paths)} fichier(s) modifié(s) ou disparu(s) depuis le "
                "scan, retiré(s) de la sélection."
            )
        self._message.setText("\n".join(lines))
        self._confirm_button.setEnabled(bool(preview.valid_paths))

    def _on_confirm_clicked(self) -> None:
        if self._preview is None or not self._preview.valid_paths:
            return
        self._confirm_button.setEnabled(False)
        self._message.setText("Suppression en cours…")
        self._viewmodel.confirm(self._preview.valid_paths, self._sizes, self._scan_root)

    def _on_deletion_finished(self, report: object) -> None:
        if not isinstance(report, DeletionReport):
            return
        self.result_report = report
        lines = [
            f"{len(report.succeeded)} fichier(s) envoyé(s) à la Corbeille "
            f"({format_bytes(report.freed_bytes)} libéré(s))."
        ]
        if report.failed:
            lines.append(f"{len(report.failed)} échec(s) :")
            lines.extend(
                f"• {path} — {reason}" for path, reason in report.failed[:_MAX_LISTED_FAILURES]
            )
        self._message.setText("\n".join(lines))
        self._confirm_button.hide()
        self._close_button.setText("Fermer")

    def _on_failed(self, message: str) -> None:
        self._message.setText(f"Erreur : {message}")
        self._confirm_button.setEnabled(False)
