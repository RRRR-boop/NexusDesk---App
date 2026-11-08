"""Mise en forme de tailles de fichiers lisibles par un humain, partagée entre les
panneaux qui affichent des octets (section 11 : DiskPilot, réutilisable par les lots
suivants)."""

from __future__ import annotations

_UNITS = ("o", "Ko", "Mo", "Go", "To")


def format_bytes(value: int) -> str:
    size = float(value)
    for unit in _UNITS[:-1]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} {_UNITS[-1]}"
