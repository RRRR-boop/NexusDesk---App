"""Dépendances Windows injectées par la racine de composition (``app.py``).

Même pattern que ``MicaApplier`` au lot 0 : ``services/`` ne doit jamais importer
``integrations/`` directement. Les formes de données (``VolumeInfoLike``,
``DeletionOutcomeLike``) sont des ``Protocol`` pour que les dataclasses concrètes de
``integrations/windows/filesystem.py`` les satisfassent par typage structurel, sans le
moindre import entre les deux couches.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol


class VolumeInfoLike(Protocol):
    @property
    def letter(self) -> str: ...
    @property
    def label(self) -> str: ...
    @property
    def filesystem(self) -> str: ...
    @property
    def volume_type(self) -> str: ...
    @property
    def total_bytes(self) -> int: ...
    @property
    def used_bytes(self) -> int: ...
    @property
    def free_bytes(self) -> int: ...


class DeletionOutcomeLike(Protocol):
    @property
    def path(self) -> str: ...
    @property
    def succeeded(self) -> bool: ...
    @property
    def error_message(self) -> str | None: ...


GetSizeOnDisk = Callable[[Path], int]
GetHardlinkKey = Callable[[Path], "tuple[int, int, int] | None"]
ListVolumes = Callable[[], "list[VolumeInfoLike]"]
SendToRecycleBin = Callable[[Sequence[Path]], "list[DeletionOutcomeLike]"]
RevealInExplorer = Callable[[Path], bool]
OpenStorageSense = Callable[[], bool]
