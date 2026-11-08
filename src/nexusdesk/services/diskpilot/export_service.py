"""Export CSV DiskPilot (section 11) : fichiers, dossiers, doublons.

Encodage ``utf-8-sig`` (BOM) pour qu'Excel sur une installation Windows en français
détecte correctement l'UTF-8 et affiche les accents sans réglage manuel.
"""

from __future__ import annotations

import csv
from pathlib import Path

from nexusdesk.models.diskpilot_domain import DuplicateGroup, FileNode, FolderNode


def export_files_csv(files: list[FileNode], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["Chemin", "Taille logique", "Taille sur disque", "Modifié le", "Catégorie"]
        )
        for node in files:
            writer.writerow(
                [
                    str(node.path),
                    node.logical_size,
                    node.size_on_disk,
                    node.modified_at.isoformat(),
                    node.category,
                ]
            )


def export_folders_csv(folders: list[FolderNode], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Chemin", "Profondeur", "Taille logique", "Taille sur disque", "Fichiers"])
        for folder in folders:
            writer.writerow(
                [
                    str(folder.path),
                    folder.depth,
                    folder.logical_size,
                    folder.size_on_disk,
                    folder.file_count,
                ]
            )


def export_duplicates_csv(groups: list[DuplicateGroup], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Taille", "Chemin", "À conserver"])
        for group in groups:
            for file_node in group.files:
                writer.writerow(
                    [
                        group.size_bytes,
                        str(file_node.path),
                        file_node.path == group.suggested_keep,
                    ]
                )
