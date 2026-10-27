"""Moteur de scan DiskPilot (section 11).

Parcours **itératif à pile explicite** sur ``os.scandir`` — jamais ``os.walk`` ni récursion
Python profonde. La détection d'identité de fichier (liens physiques) n'est appelée que
lorsque ``stat.st_nlink > 1``, et la taille réelle sur disque n'est recalculée via l'appel
Win32 coûteux que pour les fichiers compressés/creux (``FILE_ATTRIBUTE_COMPRESSED``/
``SPARSE_FILE``) : stratégies mesurées empiriquement à l'échelle réelle d'1M de fichiers
(ADR-0011). Le ramasse-miettes cyclique est désactivé pendant le parcours (aucun cycle de
référence dans ce modèle de données ; le comptage de références de CPython continue de
libérer la mémoire normalement) : son coût croît avec le nombre d'objets vivants
simultanément (jusqu'à 1M de ``FileNode``), ce qui le rendait de plus en plus coûteux à
l'approche d'1M de fichiers. Les fichiers OneDrive à la demande ne sont ni lus ni hachés.
"""

from __future__ import annotations

import gc
import heapq
import os
from datetime import datetime
from pathlib import Path

from nexusdesk.core.tasks import CancellationToken, ProgressReporter, TaskFn
from nexusdesk.models.diskpilot_domain import (
    FileNode,
    FolderNode,
    LinkEntry,
    LinkType,
    ScanOptions,
    ScanResult,
    SkippedEntry,
    SkippedKind,
    SkippedReason,
)
from nexusdesk.services.diskpilot.categorizer import categorize
from nexusdesk.services.diskpilot.exclusions import (
    build_excluded_paths,
    is_excluded,
    is_system_file,
)
from nexusdesk.services.diskpilot.ports import GetHardlinkKey, GetSizeOnDisk

_MAX_LARGEST_FILES = 1000
_MAX_SKIPPED_SAMPLE = 5000
_PROGRESS_EVERY_N_ENTRIES = 200

_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
_FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x40000
_FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x400000
_ONEDRIVE_PLACEHOLDER_MASK = _FILE_ATTRIBUTE_RECALL_ON_OPEN | _FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS

_FILE_ATTRIBUTE_SPARSE_FILE = 0x200
_FILE_ATTRIBUTE_COMPRESSED = 0x800
_SIZE_ON_DISK_MAY_DIFFER_MASK = _FILE_ATTRIBUTE_SPARSE_FILE | _FILE_ATTRIBUTE_COMPRESSED

_ERROR_FILENAME_EXCED_RANGE = 206
_ERROR_SHARING_VIOLATION = 32
_ERROR_LOCK_VIOLATION = 33


def is_onedrive_placeholder(attributes: int) -> bool:
    return bool(attributes & _ONEDRIVE_PLACEHOLDER_MASK)


def is_reparse_point(attributes: int) -> bool:
    return bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT)


def size_on_disk_may_differ_from_logical_size(attributes: int) -> bool:
    """Fichier compressé ou creux : seul cas où la taille réelle sur disque peut différer
    notablement de la taille logique. Pour tout autre fichier, l'écart possible se limite à
    l'arrondi au cluster NTFS (quelques Ko), négligeable à l'agrégat — mesuré empiriquement
    comme le second poste de coût après la détection des liens physiques (ADR-0011)."""
    return bool(attributes & _SIZE_ON_DISK_MAY_DIFFER_MASK)


def classify_os_error(exc: OSError) -> SkippedReason:
    winerror = getattr(exc, "winerror", None)
    if winerror == _ERROR_FILENAME_EXCED_RANGE:
        return "path_too_long"
    if winerror in (_ERROR_SHARING_VIOLATION, _ERROR_LOCK_VIOLATION):
        return "locked"
    return "access_denied"


def _safe_readlink(path: Path) -> Path | None:
    try:
        return Path(os.readlink(path))
    except OSError:
        return None


class _ScanAccumulator:
    def __init__(self, options: ScanOptions) -> None:
        self.options = options
        self.root_node = FolderNode(path=options.root, depth=0)
        self._folder_index: dict[Path, FolderNode] = {options.root: self.root_node}
        self.file_count = 0
        self.dir_count = 0
        self.total_logical_size = 0
        self.total_size_on_disk = 0
        self.excluded_count = 0
        self.inaccessible_count = 0
        self.onedrive_placeholder_count = 0
        self.hardlink_dedup_count = 0
        self.link_count = 0
        self.skipped: list[SkippedEntry] = []
        self.links: list[LinkEntry] = []
        self._largest_heap: list[tuple[int, int, FileNode]] = []
        self._heap_counter = 0
        self._seen_hardlinks: set[tuple[int, int, int]] = set()

    def get_or_create_folder(self, path: Path, depth: int) -> FolderNode:
        node = self._folder_index.get(path)
        if node is None:
            node = FolderNode(path=path, depth=depth)
            self._folder_index[path] = node
        return node

    def add_skipped(self, path: Path, kind: SkippedKind, reason: SkippedReason) -> None:
        if kind == "inaccessible":
            self.inaccessible_count += 1
        else:
            self.excluded_count += 1
        if len(self.skipped) < _MAX_SKIPPED_SAMPLE:
            self.skipped.append(SkippedEntry(path=path, kind=kind, reason=reason))

    def add_link(self, entry: LinkEntry) -> None:
        self.link_count += 1
        self.links.append(entry)

    def register_hardlink(self, key: tuple[int, int, int]) -> bool:
        """Renvoie True la première fois qu'une identité est vue ; False si c'est un
        chemin supplémentaire vers un fichier déjà compté (lien physique)."""
        if key in self._seen_hardlinks:
            self.hardlink_dedup_count += 1
            return False
        self._seen_hardlinks.add(key)
        return True

    def add_file(self, file_node: FileNode, folder: FolderNode) -> None:
        self.file_count += 1
        self.total_logical_size += file_node.logical_size
        self.total_size_on_disk += file_node.size_on_disk
        if file_node.is_onedrive_placeholder:
            self.onedrive_placeholder_count += 1

        folder.files.append(file_node)
        folder.file_count += 1
        folder.logical_size += file_node.logical_size
        folder.size_on_disk += file_node.size_on_disk
        folder.category_sizes[file_node.category] = (
            folder.category_sizes.get(file_node.category, 0) + file_node.logical_size
        )

        self._heap_counter += 1
        entry_tuple = (file_node.logical_size, self._heap_counter, file_node)
        if len(self._largest_heap) < _MAX_LARGEST_FILES:
            heapq.heappush(self._largest_heap, entry_tuple)
        elif entry_tuple > self._largest_heap[0]:
            heapq.heapreplace(self._largest_heap, entry_tuple)

    def largest_files(self) -> list[FileNode]:
        ordered = sorted(self._largest_heap, key=lambda item: item[0], reverse=True)
        return [node for _size, _tie, node in ordered]

    def propagate_folder_sizes(self) -> None:
        """Agrège les tailles des sous-dossiers vers leurs parents après le parcours —
        plus simple et plus sûr qu'une propagation en direct pendant la pile explicite.
        Les dossiers sont traités par profondeur décroissante : chaque enfant est donc
        toujours agrégé avant son parent."""
        for folder in sorted(self._folder_index.values(), key=lambda f: -f.depth):
            if folder is self.root_node:
                continue
            parent = self._folder_index.get(folder.path.parent)
            if parent is None:
                continue
            parent.children.append(folder)
            parent.logical_size += folder.logical_size
            parent.size_on_disk += folder.size_on_disk
            parent.file_count += folder.file_count
            for category, size in folder.category_sizes.items():
                parent.category_sizes[category] = parent.category_sizes.get(category, 0) + size


def build_scan_task(
    options: ScanOptions,
    get_size_on_disk: GetSizeOnDisk,
    get_hardlink_key: GetHardlinkKey,
) -> TaskFn:
    """Construit la fonction soumise à ``TaskManager.submit`` (pattern DiagnosticsViewModel)."""

    def _task(token: CancellationToken, reporter: ProgressReporter) -> object:
        started_at = datetime.now()
        accumulator = _ScanAccumulator(options)
        excluded_paths = build_excluded_paths(options.root)

        stack: list[tuple[Path, int]] = [(options.root, 0)]
        processed = 0

        gc_was_enabled = gc.isenabled()
        gc.disable()  # aucun cycle de référence dans ce modèle de données (ADR-0011)
        try:
            while stack:
                token.raise_if_cancelled()
                current_path, depth = stack.pop()
                folder = accumulator.get_or_create_folder(current_path, depth)
                accumulator.dir_count += 1

                try:
                    entries = list(os.scandir(current_path))
                except OSError as exc:
                    accumulator.add_skipped(current_path, "inaccessible", classify_os_error(exc))
                    continue

                for entry in entries:
                    token.raise_if_cancelled()
                    entry_path = Path(entry.path)
                    processed += 1

                    if is_excluded(entry_path, excluded_paths, options.root):
                        accumulator.add_skipped(entry_path, "excluded_default", "excluded_path")
                        continue

                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError as exc:
                        accumulator.add_skipped(entry_path, "inaccessible", classify_os_error(exc))
                        continue

                    if is_dir:
                        _handle_directory(entry, entry_path, depth, accumulator, stack)
                    else:
                        _handle_file(
                            entry,
                            entry_path,
                            folder,
                            accumulator,
                            get_size_on_disk,
                            get_hardlink_key,
                        )

                    if processed % _PROGRESS_EVERY_N_ENTRIES == 0:
                        reporter.report(
                            0.0, step=str(current_path), message=f"{processed} éléments"
                        )
        finally:
            if gc_was_enabled:
                gc.enable()

        accumulator.propagate_folder_sizes()
        finished_at = datetime.now()
        reporter.report(1.0, "terminé", f"{accumulator.file_count} fichiers")

        return ScanResult(
            scan_id=0,
            root=accumulator.root_node,
            started_at=started_at,
            finished_at=finished_at,
            status="completed",
            file_count=accumulator.file_count,
            dir_count=accumulator.dir_count,
            total_logical_size=accumulator.total_logical_size,
            total_size_on_disk=accumulator.total_size_on_disk,
            excluded_count=accumulator.excluded_count,
            inaccessible_count=accumulator.inaccessible_count,
            onedrive_placeholder_count=accumulator.onedrive_placeholder_count,
            hardlink_dedup_count=accumulator.hardlink_dedup_count,
            link_count=accumulator.link_count,
            largest_files=accumulator.largest_files(),
            skipped=accumulator.skipped,
            links=accumulator.links,
        )

    return _task


def _handle_directory(
    entry: os.DirEntry[str],
    entry_path: Path,
    depth: int,
    accumulator: _ScanAccumulator,
    stack: list[tuple[Path, int]],
) -> None:
    try:
        dir_stat = entry.stat(follow_symlinks=False)
    except OSError as exc:
        accumulator.add_skipped(entry_path, "inaccessible", classify_os_error(exc))
        return

    is_symlink = entry.is_symlink()
    if is_symlink or is_reparse_point(dir_stat.st_file_attributes):
        link_type: LinkType = "symlink" if is_symlink else "junction"
        target = _safe_readlink(entry_path)
        accumulator.add_link(LinkEntry(entry_path, link_type, target, target is None))
        return  # jamais suivi (section 11)

    stack.append((entry_path, depth + 1))


def _handle_file(
    entry: os.DirEntry[str],
    entry_path: Path,
    folder: FolderNode,
    accumulator: _ScanAccumulator,
    get_size_on_disk: GetSizeOnDisk,
    get_hardlink_key: GetHardlinkKey,
) -> None:
    if is_system_file(entry_path):
        accumulator.add_skipped(entry_path, "excluded_system_file", "excluded_path")
        return

    if entry.is_symlink():
        target = _safe_readlink(entry_path)
        accumulator.add_link(LinkEntry(entry_path, "symlink", target, target is None))
        return

    try:
        # os.stat() (pas entry.stat()) : le chemin rapide mis en cache par DirEntry sous
        # Windows renvoie toujours st_nlink == 1, peu importe les liens physiques réels.
        # Un vrai appel os.stat() est nécessaire pour une détection fiable (coût mesuré
        # empiriquement, ~34 s extrapolées à 1M fichiers, voir ADR-0011).
        stat_result = os.stat(entry_path, follow_symlinks=False)
    except OSError as exc:
        accumulator.add_skipped(entry_path, "inaccessible", classify_os_error(exc))
        return

    placeholder = is_onedrive_placeholder(stat_result.st_file_attributes)

    hardlink_key = None
    if not placeholder and stat_result.st_nlink > 1:
        hardlink_key = get_hardlink_key(entry_path)
        if hardlink_key is not None and not accumulator.register_hardlink(hardlink_key):
            return  # déjà compté via un autre chemin vers le même fichier

    if placeholder:
        # Jamais lu ni ouvert : la taille sur disque réelle est déjà connue sans
        # déclencher le moindre téléchargement (section 11).
        size_on_disk = stat_result.st_size
    elif size_on_disk_may_differ_from_logical_size(stat_result.st_file_attributes):
        try:
            size_on_disk = get_size_on_disk(entry_path)
        except OSError as exc:
            accumulator.add_skipped(entry_path, "inaccessible", classify_os_error(exc))
            return
    else:
        # Ni compressé ni creux : appeler l'API Win32 coûteuse n'apporterait qu'un
        # arrondi au cluster NTFS (quelques Ko), jamais la taille logique elle-même
        # (mesuré empiriquement comme le second poste de coût à l'échelle, ADR-0011).
        size_on_disk = stat_result.st_size

    file_node = FileNode(
        path=entry_path,
        logical_size=stat_result.st_size,
        size_on_disk=size_on_disk,
        modified_at=datetime.fromtimestamp(stat_result.st_mtime),
        category=categorize(entry_path),
        is_onedrive_placeholder=placeholder,
        hardlink_key=hardlink_key,
    )
    accumulator.add_file(file_node, folder)
