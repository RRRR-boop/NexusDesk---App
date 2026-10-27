"""Schémas pydantic des paramètres validés à la frontière interface <-> dépôt.

Seuls les onglets pertinents au lot 0 (Général, Apparence) sont modélisés ici ; les lots
suivants ajouteront un modèle par onglet de module sans toucher à ceux-ci.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

CloseBehavior = Literal["minimize", "quit"]
Theme = Literal["dark", "light", "system"]
Density = Literal["comfortable", "compact"]
TextSize = Literal["small", "medium", "large"]


class GeneralSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    launch_at_startup: bool = False
    close_behavior: CloseBehavior = "minimize"
    home_page: str = "dashboard"
    developer_mode: bool = False


class AppearanceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: Theme = "dark"
    mica_enabled: bool = True
    density: Density = "comfortable"
    text_size: TextSize = "medium"
    animations_enabled: bool = True


class DiskPilotSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extra_excluded_paths: list[str] = []
    min_duplicate_size_bytes: int = 1_048_576  # 1 Mo (section 11)
    permanent_delete_enabled: bool = False  # jamais câblé en lot 1, décoché par défaut
    warning_free_percent: float = 15.0
    alert_free_percent: float = 5.0


class AppSettings(BaseModel):
    # "ignore" (pas "forbid") : la table clé/valeur (ADR-0003) peut contenir des clés hors
    # du schéma déclaré (état d'interface comme le repli de la barre latérale, réglages des
    # lots futurs) sans faire échouer la reconstruction des onglets Général/Apparence.
    model_config = ConfigDict(extra="ignore")

    general: GeneralSettings = GeneralSettings()
    appearance: AppearanceSettings = AppearanceSettings()
    diskpilot: DiskPilotSettings = DiskPilotSettings()
