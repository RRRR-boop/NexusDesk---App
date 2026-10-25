"""Chargement des icônes SVG et reteinte selon le thème actif (section 5).

Le rendu passe par ``QSvgRenderer`` + composition ``SourceIn`` plutôt que par
``QIcon(chemin_svg)`` directement : cela évite toute dépendance au plugin Qt
``iconengines``/``qsvgicon`` dans l'exécutable packagé (risque identifié au lot 0).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = Path(__file__).resolve().parents[2] / "resources" / "icons"


def _render_tinted(svg_path: Path, size: QSize, color: str) -> QPixmap:
    renderer = QSvgRenderer(str(svg_path))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    return pixmap


def load_icon(name: str, color: str, size: int = 20) -> QIcon:
    """Charge ``resources/icons/<name>.svg`` et le reteinte en ``color``."""
    svg_path = _ICONS_DIR / f"{name}.svg"
    return QIcon(_render_tinted(svg_path, QSize(size, size), color))
