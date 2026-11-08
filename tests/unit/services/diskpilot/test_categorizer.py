from __future__ import annotations

from pathlib import Path

from nexusdesk.services.diskpilot.categorizer import categorize


def test_known_extensions_map_to_expected_category() -> None:
    assert categorize(Path("film.mp4")) == "videos"
    assert categorize(Path("photo.JPG")) == "images"
    assert categorize(Path("morceau.flac")) == "audio"
    assert categorize(Path("rapport.pdf")) == "documents"
    assert categorize(Path("archive.zip")) == "archives"
    assert categorize(Path("setup.exe")) == "installers"
    assert categorize(Path("script.py")) == "code"


def test_unknown_extension_is_other() -> None:
    assert categorize(Path("mystere.xyz")) == "other"


def test_no_extension_is_other() -> None:
    assert categorize(Path("LISEZMOI")) == "other"
