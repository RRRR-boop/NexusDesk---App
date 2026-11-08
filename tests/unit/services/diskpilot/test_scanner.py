"""Tests du moteur de scan (section 11) : liens physiques et jonctions réels sur le vrai
système de fichiers NTFS, symlinks réels avec repli si les droits manquent.

La détection de placeholder OneDrive (``is_onedrive_placeholder``) n'est testée que comme
fonction pure sur un masque de bits : une vérification empirique (``SetFileAttributesW``
avec ``FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`` sur un fichier NTFS ordinaire) a échoué avec
``ERROR_FILE_NOT_FOUND`` — cet attribut est géré par le pilote Cloud Filter réel et n'est pas
positionnable par un appel direct, donc il n'existe pas de façon fiable de simuler un vrai
placeholder sans le client OneDrive lui-même.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from nexusdesk.core.tasks import CancellationToken
from nexusdesk.integrations.windows.filesystem import get_hardlink_key, get_size_on_disk
from nexusdesk.models.diskpilot_domain import ScanOptions, ScanResult
from nexusdesk.services.diskpilot.scanner import (
    build_scan_task,
    is_onedrive_placeholder,
    is_reparse_point,
    size_on_disk_may_differ_from_logical_size,
)

_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
_FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x40000
_FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x400000


class _NullReporter:
    def report(self, fraction: float, step: str, message: str = "") -> None:
        pass


def _run_scan(root: Path, min_duplicate_size: int = 1_048_576) -> ScanResult:
    options = ScanOptions(root=root, min_duplicate_size=min_duplicate_size)
    task = build_scan_task(options, get_size_on_disk, get_hardlink_key)
    result = task(CancellationToken(), _NullReporter())
    assert isinstance(result, ScanResult)
    return result


def _can_create_symlink(tmp_path: Path) -> bool:
    target = tmp_path / "_symlink_probe_target"
    target.write_text("x")
    link = tmp_path / "_symlink_probe_link"
    try:
        os.symlink(target, link)
    except OSError:
        return False
    return True


def test_is_onedrive_placeholder_pure_bitmask() -> None:
    assert is_onedrive_placeholder(_FILE_ATTRIBUTE_RECALL_ON_OPEN) is True
    assert is_onedrive_placeholder(_FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS) is True
    assert is_onedrive_placeholder(0) is False


def test_is_reparse_point_pure_bitmask() -> None:
    assert is_reparse_point(_FILE_ATTRIBUTE_REPARSE_POINT) is True
    assert is_reparse_point(0) is False


def test_size_on_disk_may_differ_pure_bitmask() -> None:
    assert size_on_disk_may_differ_from_logical_size(0x800) is True  # COMPRESSED
    assert size_on_disk_may_differ_from_logical_size(0x200) is True  # SPARSE_FILE
    assert size_on_disk_may_differ_from_logical_size(0) is False
    assert size_on_disk_may_differ_from_logical_size(0x20) is False  # ARCHIVE seul


def test_ordinary_file_size_on_disk_skips_the_expensive_call(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "ordinaire.txt").write_bytes(b"contenu normal")

    def _boom(_path: Path) -> int:
        raise AssertionError("get_size_on_disk ne doit jamais etre appele pour ce fichier")

    options = ScanOptions(root=root)
    task = build_scan_task(options, _boom, get_hardlink_key)
    result = task(CancellationToken(), _NullReporter())

    assert isinstance(result, ScanResult)
    assert result.file_count == 1
    assert result.largest_files[0].size_on_disk == result.largest_files[0].logical_size


def test_hardlinks_are_deduplicated_in_counts_and_sizes(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    original = root / "a.txt"
    original.write_bytes(b"hello world")
    linked = root / "a_link.txt"
    os.link(original, linked)
    (root / "b.txt").write_bytes(b"other content")

    result = _run_scan(root)

    assert result.file_count == 2  # a.txt et a_link.txt comptent pour un seul fichier
    assert result.hardlink_dedup_count == 1
    assert result.total_logical_size == len(b"hello world") + len(b"other content")


def test_unlinked_files_are_not_deduplicated(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_bytes(b"hello")
    (root / "b.txt").write_bytes(b"hello")  # même contenu, mais pas de lien physique

    result = _run_scan(root)

    assert result.file_count == 2
    assert result.hardlink_dedup_count == 0


def test_junction_is_recorded_as_link_and_never_descended_into(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    real_target = tmp_path / "real_target"
    real_target.mkdir()
    (real_target / "inside.txt").write_bytes(b"ne doit jamais etre compte")

    junction = root / "lien_jonction"
    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(real_target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, f"mklink /J a echoue : {completed.stderr}"

    result = _run_scan(root)

    assert result.link_count == 1
    assert result.links[0].link_type == "junction"
    # La jonction n'est jamais suivie : le fichier a l'interieur n'est jamais compte.
    assert result.file_count == 0


@pytest.mark.skipif(
    not _can_create_symlink(Path(os.environ.get("TEMP", "."))),
    reason="droits insuffisants pour creer un symlink sur cette machine",
)
def test_symlink_is_recorded_as_link_and_never_followed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    real_target = tmp_path / "cible.txt"
    real_target.write_bytes(b"contenu reel")
    symlink = root / "lien_symbolique.txt"
    os.symlink(real_target, symlink)

    result = _run_scan(root)

    assert result.link_count == 1
    assert result.links[0].link_type == "symlink"
    assert result.file_count == 0


def test_system_file_is_skipped_not_counted(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "pagefile.sys").write_bytes(b"x")
    (root / "normal.txt").write_bytes(b"ok")

    result = _run_scan(root)

    assert result.file_count == 1  # seul normal.txt
    assert result.excluded_count == 1  # pagefile.sys


def test_excluded_folder_is_skipped_and_never_descended_into(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import nexusdesk.services.diskpilot.scanner as scanner_module

    root = tmp_path / "root"
    root.mkdir()
    (root / "normal.txt").write_bytes(b"ok")
    excluded_folder = root / "ignored"
    excluded_folder.mkdir()
    (excluded_folder / "deleted.txt").write_bytes(b"jamais compte")

    monkeypatch.setattr(
        scanner_module, "build_scan_exclusions", lambda _root, _extra: {excluded_folder}
    )

    result = _run_scan(root)

    assert result.file_count == 1
    assert result.excluded_count == 1
    assert result.inaccessible_count == 0


def test_user_excluded_folder_is_skipped_and_reported_as_user_exclusion(tmp_path: Path) -> None:
    root = tmp_path / "root"
    (root / "keep").mkdir(parents=True)
    (root / "skip").mkdir()
    (root / "keep" / "a.bin").write_bytes(b"a" * 10)
    (root / "skip" / "b.bin").write_bytes(b"b" * 10)

    options = ScanOptions(root=root, extra_excluded_paths=(root / "skip",))
    result = build_scan_task(options, get_size_on_disk, get_hardlink_key)(
        CancellationToken(), _NullReporter()
    )

    assert isinstance(result, ScanResult)
    assert result.file_count == 1
    assert [(entry.path, entry.kind) for entry in result.skipped] == [
        (root / "skip", "excluded_user")
    ]


def test_scanning_a_user_excluded_folder_explicitly_still_lists_its_content(
    tmp_path: Path,
) -> None:
    # Section 11 : un dossier exclu peut être analysé explicitement (en lecture seule).
    root = tmp_path / "excluded"
    root.mkdir()
    (root / "c.bin").write_bytes(b"c" * 10)

    options = ScanOptions(root=root, extra_excluded_paths=(root,))
    result = build_scan_task(options, get_size_on_disk, get_hardlink_key)(
        CancellationToken(), _NullReporter()
    )

    assert isinstance(result, ScanResult)
    assert result.file_count == 1
    assert result.excluded_count == 0
