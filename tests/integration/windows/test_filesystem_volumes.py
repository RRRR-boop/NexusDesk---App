"""Volumes réels de cette machine (section 11) : aucune donnée simulée."""

from __future__ import annotations

from nexusdesk.integrations.windows.filesystem import list_volumes


def test_system_drive_is_listed_with_plausible_values() -> None:
    volumes = list_volumes()

    system_drive = next((v for v in volumes if v.letter.upper().startswith("C:")), None)
    assert system_drive is not None, "le volume C: devrait toujours etre present"
    assert system_drive.total_bytes > 0
    assert 0 <= system_drive.free_bytes <= system_drive.total_bytes
    assert system_drive.used_bytes == system_drive.total_bytes - system_drive.free_bytes
    assert system_drive.volume_type == "fixed"
    assert system_drive.filesystem  # non vide


def test_no_volume_has_negative_or_implausible_sizes() -> None:
    for volume in list_volumes():
        assert volume.total_bytes >= 0
        assert volume.free_bytes >= 0
        assert volume.used_bytes >= 0
