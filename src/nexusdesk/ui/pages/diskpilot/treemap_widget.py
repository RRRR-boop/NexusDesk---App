"""Treemap squarifié (Bruls, Huizing, van Wijk — section 11) : widget ``QPainter`` pur,
aucune dépendance à une bibliothèque de graphes. La mise en page est mise en cache et
recalculée seulement au redimensionnement ou au changement de dossier affiché — jamais à
chaque ``paintEvent`` — et le treemap n'est jamais rafraîchi pendant un scan en direct
(seulement à la réception de ``scan_finished``), pour éviter tout gel par redessin excessif.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QMouseEvent, QPainter, QPaintEvent, QResizeEvent
from PySide6.QtWidgets import QWidget

from nexusdesk.models.diskpilot_domain import FolderNode
from nexusdesk.ui.theme.tokens import CATEGORY_COLORS, DARK_COLORS, ColorTokens

_MAX_RENDERED_ITEMS = 200
_OTHERS_LABEL = "Autres"


@dataclass(frozen=True)
class _TreemapItem:
    label: str
    size: int
    color: str
    folder: FolderNode | None  # None pour un fichier ou le bucket « Autres »


def _worst_ratio(row_values: list[float], side: float) -> float:
    if side <= 0:
        return float("inf")
    total = sum(row_values)
    if total <= 0:
        return float("inf")
    row_length = total / side
    if row_length <= 0:
        return float("inf")
    worst = 0.0
    for value in row_values:
        if value <= 0:
            continue
        item_side = value / row_length
        worst = max(worst, max(item_side / side, side / item_side))
    return worst


def squarify(
    values: list[float], x: float, y: float, w: float, h: float
) -> list[tuple[float, float, float, float]]:
    """Construit des rangées de rectangles en minimisant le pire ratio largeur/hauteur à
    chaque étape, perpendiculairement au côté le plus court du rectangle restant. Renvoie
    les rectangles ``(x, y, w, h)`` dans le même ordre que ``values``."""
    if not values or w <= 0 or h <= 0:
        return [(x, y, 0.0, 0.0) for _ in values]
    total = sum(values)
    if total <= 0:
        return [(x, y, 0.0, 0.0) for _ in values]
    scale = (w * h) / total
    scaled = [max(value, 0.0) * scale for value in values]

    result: dict[int, tuple[float, float, float, float]] = {}
    remaining = list(enumerate(scaled))
    rx, ry, rw, rh = x, y, w, h

    while remaining:
        side = min(rw, rh)
        row = [remaining[0]]
        best_worst = _worst_ratio([row[0][1]], side)
        consumed = 1
        for next_item in remaining[1:]:
            candidate_values = [value for _, value in row] + [next_item[1]]
            candidate_worst = _worst_ratio(candidate_values, side)
            if candidate_worst > best_worst:
                break
            row.append(next_item)
            best_worst = candidate_worst
            consumed += 1

        row_sum = sum(value for _, value in row)
        row_length = row_sum / side if side > 0 else 0.0
        horizontal = rw >= rh
        offset = 0.0
        for idx, value in row:
            item_side = value / row_length if row_length > 0 else 0.0
            if horizontal:
                result[idx] = (rx, ry + offset, row_length, item_side)
            else:
                result[idx] = (rx + offset, ry, item_side, row_length)
            offset += item_side

        remaining = remaining[consumed:]
        if horizontal:
            rx += row_length
            rw -= row_length
        else:
            ry += row_length
            rh -= row_length

    return [result[i] for i in range(len(values))]


def _build_items(folder: FolderNode) -> list[_TreemapItem]:
    items: list[_TreemapItem] = []
    for child in folder.children:
        if child.logical_size > 0:
            label = child.path.name or str(child.path)
            items.append(_TreemapItem(label, child.logical_size, "", child))
    for file_node in folder.files:
        if file_node.logical_size > 0:
            color = CATEGORY_COLORS.get(file_node.category, CATEGORY_COLORS["other"])
            items.append(_TreemapItem(file_node.path.name, file_node.logical_size, color, None))

    items.sort(key=lambda item: item.size, reverse=True)
    if len(items) <= _MAX_RENDERED_ITEMS:
        return items
    kept = items[:_MAX_RENDERED_ITEMS]
    rest_size = sum(item.size for item in items[_MAX_RENDERED_ITEMS:])
    if rest_size > 0:
        kept.append(_TreemapItem(_OTHERS_LABEL, rest_size, "", None))
    return kept


class TreemapWidget(QWidget):
    folder_opened = Signal(object)  # FolderNode

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(240)
        self._colors: ColorTokens = DARK_COLORS
        self._items: list[_TreemapItem] = []
        self._rects: list[tuple[float, float, float, float]] = []

    def set_folder(self, folder: FolderNode | None, colors: ColorTokens) -> None:
        self._colors = colors
        self._items = _build_items(folder) if folder is not None else []
        self._recompute_layout()
        self.update()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - signature imposée par Qt
        super().resizeEvent(event)
        self._recompute_layout()

    def _recompute_layout(self) -> None:
        if not self._items:
            self._rects = []
            return
        sizes = [float(item.size) for item in self._items]
        self._rects = squarify(sizes, 0.0, 0.0, float(self.width()), float(self.height()))

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - signature imposée par Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        metrics = QFontMetrics(painter.font())
        for item, (rx, ry, rw, rh) in zip(self._items, self._rects, strict=True):
            if rw < 1 or rh < 1:
                continue
            rect = QRectF(rx, ry, rw, rh)
            fill_color = self._colors.bg_raised if not item.color else item.color
            painter.fillRect(rect, QColor(fill_color))
            painter.setPen(QColor(self._colors.border_subtle))
            painter.drawRect(rect)
            if rw > 36 and rh > 16:
                painter.setPen(QColor(self._colors.text_primary))
                elided = metrics.elidedText(item.label, Qt.TextElideMode.ElideRight, int(rw) - 8)
                painter.drawText(
                    rect.adjusted(4, 2, -4, -2),
                    int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop),
                    elided,
                )
        painter.end()

    def mouseDoubleClickEvent(  # noqa: N802 - signature imposée par Qt
        self, event: QMouseEvent
    ) -> None:
        position = event.position()
        for item, (rx, ry, rw, rh) in zip(self._items, self._rects, strict=True):
            if rx <= position.x() <= rx + rw and ry <= position.y() <= ry + rh:
                if item.folder is not None:
                    self.folder_opened.emit(item.folder)
                return
