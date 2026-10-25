"""Génération du QSS à partir des jetons (ADR-0004 : assemblage Python natif, pas de
moteur de templates — aucune dépendance hors de la stack listée section 3)."""

from __future__ import annotations

from nexusdesk.config.schema import Density, TextSize
from nexusdesk.ui.theme.tokens import RADIUS, SPACING, TYPOGRAPHY, ColorTokens

_DENSITY_PADDING = {"comfortable": 10, "compact": 6}
_TEXT_SIZE_DELTA_PX = {"small": -1, "medium": 0, "large": 2}


def build_qss(
    colors: ColorTokens,
    density: Density = "comfortable",
    text_size: TextSize = "medium",
) -> str:
    padding = _DENSITY_PADDING[density]
    body_size = TYPOGRAPHY.body.size_px + _TEXT_SIZE_DELTA_PX[text_size]

    return f"""
QWidget {{
    background-color: {colors.bg_base};
    color: {colors.text_primary};
    font-family: "{TYPOGRAPHY.body.family}";
    font-size: {body_size}px;
}}

QMainWindow {{
    background-color: {colors.bg_base};
}}

QLabel[role="pageTitle"] {{
    font-family: "{TYPOGRAPHY.page_title.family}";
    font-size: {TYPOGRAPHY.page_title.size_px}px;
    font-weight: {TYPOGRAPHY.page_title.weight};
    color: {colors.text_primary};
}}

QLabel[role="sectionTitle"] {{
    font-family: "{TYPOGRAPHY.section_title.family}";
    font-size: {TYPOGRAPHY.section_title.size_px}px;
    font-weight: {TYPOGRAPHY.section_title.weight};
}}

QLabel[role="caption"] {{
    font-family: "{TYPOGRAPHY.caption.family}";
    font-size: {TYPOGRAPHY.caption.size_px}px;
    color: {colors.text_secondary};
}}

QLabel[role="data"] {{
    font-family: "{TYPOGRAPHY.data.family}";
    font-size: {TYPOGRAPHY.data.size_px}px;
}}

QWidget[role="card"] {{
    background-color: {colors.bg_surface};
    border: 1px solid {colors.border_subtle};
    border-radius: {RADIUS.card}px;
}}

QPushButton {{
    background-color: {colors.bg_raised};
    color: {colors.text_primary};
    border: 1px solid {colors.border_subtle};
    border-radius: {RADIUS.control}px;
    padding: {padding}px {padding + 4}px;
}}

QPushButton:hover {{
    border-color: {colors.accent_primary};
}}

QPushButton:disabled {{
    color: {colors.text_disabled};
}}

QPushButton[role="primary"] {{
    background-color: {colors.accent_primary};
    color: #FFFFFF;
    border: none;
}}

QPushButton[role="primary"]:hover {{
    background-color: {colors.accent_primary_hover};
}}

QLineEdit, QComboBox {{
    background-color: {colors.bg_surface};
    color: {colors.text_primary};
    border: 1px solid {colors.border_subtle};
    border-radius: {RADIUS.control}px;
    padding: {padding - 2}px {padding}px;
}}

QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {colors.accent_primary};
}}

QListWidget#navigationList {{
    background-color: {colors.bg_surface};
    border: none;
    outline: none;
}}

QListWidget#navigationList::item {{
    padding: {padding}px {SPACING.sm}px;
    border-radius: {RADIUS.control}px;
}}

QListWidget#navigationList::item:selected {{
    background-color: {colors.accent_primary};
    color: #FFFFFF;
}}

QListWidget#navigationList::item:hover:!selected {{
    background-color: {colors.bg_raised};
}}

QTabWidget::pane {{
    border: 1px solid {colors.border_subtle};
    border-radius: {RADIUS.card}px;
}}

QTabBar::tab {{
    background-color: {colors.bg_surface};
    color: {colors.text_secondary};
    padding: {padding}px {SPACING.md}px;
}}

QTabBar::tab:selected {{
    color: {colors.text_primary};
    border-bottom: 2px solid {colors.accent_primary};
}}

QScrollBar:vertical {{
    background-color: {colors.bg_base};
    width: 10px;
}}

QScrollBar::handle:vertical {{
    background-color: {colors.border_subtle};
    border-radius: {RADIUS.control}px;
    min-height: 24px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QMenu {{
    background-color: {colors.bg_raised};
    color: {colors.text_primary};
    border: 1px solid {colors.border_subtle};
}}

QMenu::item:selected {{
    background-color: {colors.accent_primary};
    color: #FFFFFF;
}}

QToolTip {{
    background-color: {colors.bg_raised};
    color: {colors.text_primary};
    border: 1px solid {colors.border_subtle};
}}

QCheckBox {{
    spacing: {SPACING.xs}px;
}}
"""
