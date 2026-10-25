from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base déclarative partagée par toutes les entités SQLAlchemy de nexusdesk.db."""
