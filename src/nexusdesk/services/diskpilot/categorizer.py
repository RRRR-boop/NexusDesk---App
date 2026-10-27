"""Classification par catégorie d'après l'extension (section 11), fonction pure."""

from __future__ import annotations

from pathlib import Path

from nexusdesk.models.diskpilot_domain import Category

_EXTENSION_CATEGORIES: dict[str, Category] = {}


def _register(category: Category, extensions: set[str]) -> None:
    for extension in extensions:
        _EXTENSION_CATEGORIES[extension] = category


_register("videos", {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg"})
_register(
    "images",
    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic", ".tiff", ".ico"},
)
_register("audio", {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"})
_register(
    "documents",
    {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".odt",
        ".ods",
        ".rtf",
    },
)
_register("archives", {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso", ".xz"})
_register("installers", {".exe", ".msi", ".msix", ".appx", ".msixbundle"})
_register(
    "code",
    {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".html",
        ".css",
        ".json",
        ".yaml",
        ".yml",
        ".md",
        ".sql",
        ".ps1",
        ".sh",
    },
)


def categorize(path: Path) -> Category:
    return _EXTENSION_CATEGORIES.get(path.suffix.lower(), "other")
