"""Chargement des icônes SVG et reteinte selon le thème actif (section 5).

Le rendu passe par ``QSvgRenderer`` + composition ``SourceIn`` plutôt que par
``QIcon(chemin_svg)`` directement : cela évite toute dépendance au plugin Qt
``iconengines``/``qsvgicon`` dans l'exécutable packagé (risque identifié au lot 0).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
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


# Icône de marque : glyphe officiel (app.svg) en blanc sur un carré arrondi violet (jeton
# accent_primary). Source unique de la fenêtre, de la barre des tâches et du fichier app.ico
# de l'exécutable et de l'installateur (généré par scripts/make_icon.py).
APP_ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
_BRAND_BACKGROUND = "#7C3AED"
_BRAND_GLYPH = "#FFFFFF"


def render_app_icon(size: int) -> QImage:
    """Rend l'icône de marque en ``size`` x ``size`` (QImage : utilisable sans QGuiApplication)."""
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(_BRAND_BACKGROUND))
    radius = size * 0.22
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    # Glyphe teinté en blanc sur une couche séparée, puis centré avec une marge de 20 %.
    margin = round(size * 0.2)
    glyph_size = size - 2 * margin
    glyph = QImage(glyph_size, glyph_size, QImage.Format.Format_ARGB32_Premultiplied)
    glyph.fill(Qt.GlobalColor.transparent)
    glyph_painter = QPainter(glyph)
    glyph_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(str(_ICONS_DIR / "app.svg")).render(glyph_painter)
    glyph_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    glyph_painter.fillRect(glyph.rect(), QColor(_BRAND_GLYPH))
    glyph_painter.end()

    painter.drawImage(margin, margin, glyph)
    painter.end()
    return image


def load_app_icon() -> QIcon:
    """Icône de marque multirésolution pour les fenêtres et la barre des tâches."""
    icon = QIcon()
    for size in APP_ICON_SIZES:
        icon.addPixmap(QPixmap.fromImage(render_app_icon(size)))
    return icon
