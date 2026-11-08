"""Génère THIRD-PARTY-LICENSES.txt pour une distribution de NexusDesk.

Appelé par scripts/package-release.ps1 avec la liste des dépendances d'exécution (celles
embarquées dans l'exécutable). Lit directement les métadonnées installées plutôt que
pip-licenses, qui ne comprend pas encore l'expression SPDX ``License-Expression`` (PEP 639)
et affichait « UNKNOWN » pour une partie des paquets.

Usage : python scripts/third_party_licenses.py --version 0.2.1-beta.2 --output FICHIER PAQUET...
"""

from __future__ import annotations

import argparse
import platform
import sys
from importlib import metadata
from pathlib import Path

_REPO_URL = "https://github.com/RRRR-boop/NexusDesk---App"
_LICENSES_DIR = Path(__file__).resolve().parent.parent / "licenses"
_RULE = "-" * 78


def _license_name(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    expression = meta.get("License-Expression")
    if expression:
        return str(expression)
    classifiers = [
        c.split("::")[-1].strip()
        for c in meta.get_all("Classifier") or []
        if c.startswith("License ::")
    ]
    if classifiers:
        return " / ".join(classifiers)
    short = (meta.get("License") or "").strip()
    return short if short and "\n" not in short else "voir le texte ci-dessous"


def _license_texts(dist: metadata.Distribution) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []
    for file in dist.files or []:
        parts = [part.lower() for part in file.parts]
        name = parts[-1]
        in_dist_info = parts[0].endswith(".dist-info")
        is_license = in_dist_info and (
            "licenses" in parts or name.startswith(("license", "licence", "copying", "notice"))
        )
        if is_license:
            content = Path(str(file.locate())).read_text(encoding="utf-8", errors="replace")
            texts.append((str(file), content.strip()))
    return texts


def build(version: str, packages: list[str]) -> str:
    out: list[str] = [
        f"NexusDesk {version} - avis de licences",
        "=" * 78,
        "",
        "NexusDesk est un logiciel libre distribué sous la GNU General Public License v3.0",
        "(GPL-3.0-only) : texte intégral dans le fichier LICENSE de cette distribution.",
        f"Code source correspondant à cette version : {_REPO_URL}/tree/v{version}",
        "",
        "Composants tiers embarqués, chacun sous sa propre licence, toutes compatibles avec la",
        "GPL v3. Qt / PySide6 / shiboken6 sont utilisés sous LGPL v3 (texte intégral en fin de",
        "fichier) : leurs bibliothèques sont livrées comme fichiers séparés dans le dossier",
        "_internal et peuvent être remplacées par une version modifiée compatible. Le chargeur",
        "PyInstaller est distribué sous GPL v2 avec une exception explicite autorisant toute",
        "licence pour le programme empaqueté.",
        "",
    ]

    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    out += [
        _RULE,
        f"Interpréteur Python {platform.python_version()} (DLL et bibliothèque standard)",
    ]
    out.append(_RULE)
    if python_license.exists():
        out.append(python_license.read_text(encoding="utf-8").strip())
    else:
        out.append("Python Software Foundation License (PSF-2.0)")
    out.append("")

    missing: list[str] = []
    for package in sorted(set(packages), key=str.lower):
        dist = metadata.distribution(package)
        title = f"{dist.metadata['Name']} {dist.version} - licence : {_license_name(dist)}"
        out += [_RULE, title, _RULE]
        texts = _license_texts(dist)
        if not texts:
            missing.append(package)
            out.append(
                "(aucun fichier de licence fourni par le paquet ; licence indiquée ci-dessus)"
            )
        for path, text in texts:
            out += [f"[{path}]", text, ""]
        out.append("")

    lgpl = _LICENSES_DIR / "LGPL-3.0.txt"
    out += [_RULE, "GNU Lesser General Public License v3.0 (Qt, PySide6, shiboken6)", _RULE]
    out.append(lgpl.read_text(encoding="utf-8").strip())
    if missing:
        print("Sans fichier de licence propre : " + ", ".join(missing), file=sys.stderr)
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("packages", nargs="+")
    args = parser.parse_args()
    args.output.write_text(build(args.version, args.packages), encoding="utf-8")


if __name__ == "__main__":
    main()
