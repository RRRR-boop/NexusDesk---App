"""Jetons de design définis une seule fois (section 5) ; aucun widget ne doit coder en dur
une couleur, une taille ou une durée d'animation — tout passe par ce module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ThemeName = Literal["dark", "light"]


@dataclass(frozen=True)
class ColorTokens:
    bg_base: str
    bg_surface: str
    bg_raised: str
    border_subtle: str
    text_primary: str
    text_secondary: str
    text_disabled: str
    accent_primary: str
    accent_primary_hover: str
    accent_secondary: str
    status_success: str
    status_warning: str
    status_danger: str


DARK_COLORS = ColorTokens(
    bg_base="#16161A",
    bg_surface="#1E1E24",
    bg_raised="#26262E",
    border_subtle="#33333D",
    text_primary="#EDEDF2",
    text_secondary="#A6A6B5",
    text_disabled="#6E6E7E",
    accent_primary="#7C3AED",
    accent_primary_hover="#8B5CF6",
    accent_secondary="#22D3EE",
    status_success="#34D399",
    status_warning="#FBBF24",
    status_danger="#F87171",
)

# Thème clair : mêmes rôles sémantiques, inversés en luminosité, mêmes teintes d'accent
# (contrastes à vérifier WCAG AA comme pour le thème sombre, cf. section 5).
LIGHT_COLORS = ColorTokens(
    bg_base="#F7F7FA",
    bg_surface="#FFFFFF",
    bg_raised="#EDEDF2",
    border_subtle="#D8D8E0",
    text_primary="#16161A",
    text_secondary="#4B4B59",
    text_disabled="#9A9AA8",
    accent_primary="#7C3AED",
    accent_primary_hover="#6D28D9",
    accent_secondary="#0E7490",
    status_success="#059669",
    status_warning="#B45309",
    status_danger="#DC2626",
)


def colors_for(theme: ThemeName) -> ColorTokens:
    return DARK_COLORS if theme == "dark" else LIGHT_COLORS


@dataclass(frozen=True)
class Spacing:
    """Grille de 4 px (section 5)."""

    xxs: int = 4
    xs: int = 8
    sm: int = 12
    md: int = 16
    lg: int = 24
    xl: int = 32
    page_margin: int = 24
    card_gap: int = 16


@dataclass(frozen=True)
class Radius:
    control: int = 4
    card: int = 8


@dataclass(frozen=True)
class FontSpec:
    family: str
    size_px: int
    weight: int


@dataclass(frozen=True)
class Typography:
    page_title: FontSpec = FontSpec("Segoe UI Variable Display", 28, 600)
    section_title: FontSpec = FontSpec("Segoe UI Variable", 20, 600)
    subtitle: FontSpec = FontSpec("Segoe UI Variable", 16, 600)
    body: FontSpec = FontSpec("Segoe UI Variable Text", 14, 400)
    caption: FontSpec = FontSpec("Segoe UI Variable Small", 12, 400)
    data: FontSpec = FontSpec("Cascadia Mono", 13, 400)
    key_figure: FontSpec = FontSpec("Segoe UI Variable Display", 32, 600)


@dataclass(frozen=True)
class Motion:
    duration_ms: int = 180
    easing: str = "ease-out"


SPACING = Spacing()
RADIUS = Radius()
TYPOGRAPHY = Typography()
MOTION = Motion()

# Couleurs par catégorie DiskPilot (section 11), stables entre les deux thèmes pour rester
# reconnaissables (treemap, répartition). Clés en chaîne brute plutôt qu'en important le
# type Category de models/ : ui/theme/ reste une fondation sans dépendance vers le haut.
CATEGORY_COLORS: dict[str, str] = {
    "videos": "#F472B6",
    "images": "#22D3EE",
    "audio": "#A78BFA",
    "documents": "#60A5FA",
    "archives": "#FBBF24",
    "installers": "#F87171",
    "code": "#34D399",
    "other": "#9CA3AF",
}
