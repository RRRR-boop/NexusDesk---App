from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from nexusdesk.models.base import Base


class SettingRow(Base):
    """Stockage clé/valeur des paramètres (ADR-0003) : une ligne par réglage à plat.

    La valeur JSON et la table clé/valeur évitent une migration Alembic à chaque réglage
    ajouté par les lots suivants.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
