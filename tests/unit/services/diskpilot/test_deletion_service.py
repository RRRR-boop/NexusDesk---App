from __future__ import annotations

import time
from pathlib import Path

import pytest
import win32con
import win32file

from nexusdesk.services.diskpilot.deletion_service import (
    build_preview,
    execute_deletion,
    filter_refused,
)


def test_preview_retains_untouched_files_and_sums_their_size(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    a.write_bytes(b"contenu a")
    stat = a.stat()

    preview = build_preview([a], {a: stat.st_size}, {a: stat.st_mtime})

    assert preview.valid_paths == [a]
    assert preview.changed_paths == []
    assert preview.total_size == stat.st_size


def test_preview_flags_file_modified_since_scan(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    a.write_bytes(b"contenu original")
    original_size = a.stat().st_size

    time.sleep(0.05)
    a.write_bytes(b"contenu change, taille differente !")

    preview = build_preview([a], {a: original_size}, {})

    assert preview.valid_paths == []
    assert preview.changed_paths == [a]


def test_preview_flags_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "disparu.txt"

    preview = build_preview([missing], {}, {})

    assert preview.changed_paths == [missing]


def test_filter_refused_rejects_system_file(tmp_path: Path) -> None:
    pagefile = tmp_path / "pagefile.sys"
    pagefile.write_bytes(b"x")

    allowed, refused = filter_refused([pagefile], scan_root=tmp_path)

    assert allowed == []
    assert refused[0][0] == pagefile


def test_file_in_protected_folder_stays_refused_even_when_that_folder_was_scanned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Un dossier exclu peut être analysé explicitement (section 11), mais en lecture seule :
    # aucun fichier situé dessous ne doit devenir supprimable. Chemin non créé : le refus
    # pour chemin exclu intervient avant toute ouverture du fichier.
    monkeypatch.setenv("SYSTEMDRIVE", tmp_path.drive)
    program_files = Path(tmp_path.drive + "\\Program Files")
    target = program_files / "Editeur" / "app.dll"

    allowed, refused = filter_refused([target], scan_root=program_files)

    assert allowed == []
    assert refused == [(target, "Chemin exclu par défaut.")]


def test_filter_refused_rejects_locked_file(tmp_path: Path) -> None:
    locked = tmp_path / "locked.bin"
    locked.write_bytes(b"verrouille")

    # Partage 0 (exclusif) : seul un vrai verrou de partage Windows, pas un simple verrou
    # d'octets, fait échouer un open() ultérieur venant d'un autre descripteur.
    handle = win32file.CreateFile(
        str(locked),
        win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        0,
        None,
        win32con.OPEN_EXISTING,
        0,
        None,
    )
    try:
        allowed, refused = filter_refused([locked], scan_root=tmp_path)
    finally:
        win32file.CloseHandle(handle)

    assert allowed == []
    assert refused[0][0] == locked


def test_execute_deletion_reports_partial_success(tmp_path: Path) -> None:
    succeeded_path = tmp_path / "ok.txt"
    succeeded_path.write_bytes(b"x")
    failed_path = tmp_path / "echec.txt"
    failed_path.write_bytes(b"xx")

    class _Outcome:
        def __init__(self, path: str, succeeded: bool, error_message: str | None) -> None:
            self.path = path
            self.succeeded = succeeded
            self.error_message = error_message

    def _fake_send_to_recycle_bin(paths: object) -> list[_Outcome]:
        return [
            _Outcome(str(succeeded_path), True, None),
            _Outcome(str(failed_path), False, "Code d'erreur Windows 5"),
        ]

    report = execute_deletion(
        [succeeded_path, failed_path],
        {succeeded_path: 100, failed_path: 200},
        scan_root=tmp_path,
        send_to_recycle_bin=_fake_send_to_recycle_bin,
    )

    assert report.succeeded == [succeeded_path]
    assert report.freed_bytes == 100
    assert report.failed == [(failed_path, "Code d'erreur Windows 5")]
