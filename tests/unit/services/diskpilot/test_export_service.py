from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from nexusdesk.models.diskpilot_domain import DuplicateGroup, FileNode, FolderNode
from nexusdesk.services.diskpilot.export_service import (
    export_duplicates_csv,
    export_files_csv,
    export_folders_csv,
)

_NOW = datetime(2026, 10, 27, 10, 30)


def _read_csv(destination: Path) -> list[list[str]]:
    with destination.open(encoding="utf-8-sig") as handle:
        return list(csv.reader(handle))


def test_export_files_csv_writes_header_and_rows(tmp_path: Path) -> None:
    node = FileNode(
        path=Path(r"C:\accentué\fichier.txt"),
        logical_size=42,
        size_on_disk=42,
        modified_at=_NOW,
        category="documents",
    )
    destination = tmp_path / "files.csv"

    export_files_csv([node], destination)
    rows = _read_csv(destination)

    assert rows[0] == ["Chemin", "Taille logique", "Taille sur disque", "Modifié le", "Catégorie"]
    assert rows[1][0] == r"C:\accentué\fichier.txt"
    assert rows[1][4] == "documents"


def test_export_folders_csv_writes_header_and_rows(tmp_path: Path) -> None:
    folder = FolderNode(path=Path(r"C:\dossier"), depth=1, logical_size=123, file_count=3)
    destination = tmp_path / "folders.csv"

    export_folders_csv([folder], destination)
    rows = _read_csv(destination)

    assert rows[0] == ["Chemin", "Profondeur", "Taille logique", "Taille sur disque", "Fichiers"]
    assert rows[1] == [r"C:\dossier", "1", "123", "0", "3"]


def test_export_duplicates_csv_flags_the_suggested_keep(tmp_path: Path) -> None:
    keep = FileNode(
        path=Path(r"C:\keep.txt"),
        logical_size=10,
        size_on_disk=10,
        modified_at=_NOW,
        category="other",
    )
    extra = FileNode(
        path=Path(r"C:\extra.txt"),
        logical_size=10,
        size_on_disk=10,
        modified_at=_NOW,
        category="other",
    )
    group = DuplicateGroup(
        size_bytes=10, files=[keep, extra], suggested_keep=keep.path, recoverable_bytes=10
    )
    destination = tmp_path / "duplicates.csv"

    export_duplicates_csv([group], destination)
    rows = _read_csv(destination)

    assert rows[0] == ["Taille", "Chemin", "À conserver"]
    data_rows = {row[1]: row[2] for row in rows[1:]}
    assert data_rows[r"C:\keep.txt"] == "True"
    assert data_rows[r"C:\extra.txt"] == "False"
