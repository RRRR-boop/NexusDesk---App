"""Conteneur de composition des viewmodels DiskPilot (section 11) : point d'entrée unique
injecté dans la page, construit une seule fois par ``app.py``. Pas de logique propre."""

from __future__ import annotations

from nexusdesk.viewmodels.diskpilot_cleanup_viewmodel import CleanupSuggestionsViewModel
from nexusdesk.viewmodels.diskpilot_deletion_viewmodel import DeletionViewModel
from nexusdesk.viewmodels.diskpilot_duplicates_viewmodel import DuplicatesViewModel
from nexusdesk.viewmodels.diskpilot_history_viewmodel import ScanHistoryViewModel
from nexusdesk.viewmodels.diskpilot_scan_viewmodel import ScanViewModel
from nexusdesk.viewmodels.diskpilot_volumes_viewmodel import VolumesViewModel


class DiskPilotViewModel:
    def __init__(
        self,
        volumes: VolumesViewModel,
        scan: ScanViewModel,
        duplicates: DuplicatesViewModel,
        deletion: DeletionViewModel,
        cleanup: CleanupSuggestionsViewModel,
        history: ScanHistoryViewModel,
    ) -> None:
        self.volumes = volumes
        self.scan = scan
        self.duplicates = duplicates
        self.deletion = deletion
        self.cleanup = cleanup
        self.history = history
