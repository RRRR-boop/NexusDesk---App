"""Hiérarchie d'erreurs typées partagée par toutes les couches métier."""

from __future__ import annotations


class NexusDeskError(Exception):
    """Base de toutes les erreurs connues de NexusDesk."""


class DependencyMissing(NexusDeskError):
    """Un composant externe requis (WinGet, Tesseract, module PowerShell...) est absent."""


class PermissionDenied(NexusDeskError):
    """L'opération a été refusée par le système (droits insuffisants)."""


class Timeout(NexusDeskError):
    """L'opération a dépassé le délai autorisé."""


class Cancelled(NexusDeskError):
    """L'opération a été annulée par l'utilisateur via son jeton d'annulation."""
