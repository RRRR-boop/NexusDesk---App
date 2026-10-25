"""Configuration globale : les tests ne doivent pas afficher de vraies fenêtres ni voler le
focus sur le poste qui les exécute (plateforme Qt « offscreen »)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
