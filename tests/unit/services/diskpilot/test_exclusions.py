from __future__ import annotations

from pathlib import Path

import pytest

from nexusdesk.services.diskpilot.exclusions import (
    build_excluded_paths,
    is_excluded,
    is_system_file,
)


def test_is_system_file_matches_known_names_case_insensitively() -> None:
    assert is_system_file(Path(r"C:\pagefile.sys"))
    assert is_system_file(Path(r"C:\HIBERFIL.SYS"))
    assert not is_system_file(Path(r"C:\notes.txt"))


def test_scan_root_is_exempt_but_nested_system_folder_is_not(tmp_path: Path) -> None:
    # Les dossiers système par défaut (ADR : exclusions.py) sont des chemins absolus à la
    # racine du volume ; pour tester l'exemption de la racine de scan, celle-ci doit donc
    # être l'un de ces chemins — l'existence réelle du dossier n'est pas requise, la
    # fonction est pure et ne touche jamais le disque.
    scan_root = Path(tmp_path.drive + "\\$Recycle.Bin")
    excluded = build_excluded_paths(scan_root)

    assert is_excluded(scan_root, excluded, scan_root) is False
    nested = scan_root / "S-1-5-21" / "file.bin"
    assert is_excluded(nested, excluded, scan_root) is True


def test_system_drive_adds_windows_and_program_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    drive = tmp_path.drive
    monkeypatch.setenv("SYSTEMDRIVE", drive)

    excluded = build_excluded_paths(tmp_path)

    assert Path(drive + "\\Windows") in excluded
    assert Path(drive + "\\Program Files") in excluded


def test_non_system_drive_does_not_add_windows_and_program_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other_drive = "Z:" if tmp_path.drive.upper() != "Z:" else "Y:"
    monkeypatch.setenv("SYSTEMDRIVE", other_drive)

    excluded = build_excluded_paths(tmp_path)

    assert Path(tmp_path.drive + "\\Windows") not in excluded
    assert Path(tmp_path.drive + "\\$Recycle.Bin") in excluded
