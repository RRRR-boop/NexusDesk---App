"""Cache d'empreintes DiskPilot : base SQLite séparée sous ``core/paths.get_cache_dir()``,
hors de la chaîne Alembic principale (ADR-0015) — donnée dérivée et jetable, pas de
migration versionnée nécessaire."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CacheBase(DeclarativeBase):
    """Base déclarative dédiée au cache, distincte de ``models.base.Base``."""


class FileHashCache(CacheBase):
    __tablename__ = "hash_cache"

    path: Mapped[str] = mapped_column(primary_key=True)
    size: Mapped[int]
    mtime: Mapped[float]
    partial_sha256: Mapped[str | None]
    full_sha256: Mapped[str | None]
    last_seen_at: Mapped[datetime]
