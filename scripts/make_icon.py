"""Génère src/nexusdesk/resources/icons/app.ico (icône multirésolution de NexusDesk.exe).

Les images viennent de ``render_app_icon`` (ui/theme/icon_provider.py), la même source que
l'icône des fenêtres : l'exécutable, l'installateur, les raccourcis et la barre des tâches
affichent donc exactement le même visuel. Chaque taille est stockée en PNG dans le conteneur
ICO (pris en charge par Windows depuis Vista), sans dépendance supplémentaire.

Usage : uv run python scripts/make_icon.py
"""

from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice

from nexusdesk.ui.theme.icon_provider import APP_ICON_SIZES, render_app_icon

_OUTPUT = Path(__file__).resolve().parent.parent / "src/nexusdesk/resources/icons/app.ico"


def _png_bytes(size: int) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not render_app_icon(size).save(buffer, b"PNG"):
        raise RuntimeError(f"Échec de l'encodage PNG en {size} px")
    buffer.close()
    return bytes(data.data())


def build_ico() -> bytes:
    images = [(size, _png_bytes(size)) for size in APP_ICON_SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))  # réservé, type 1 = icône, nombre
    directory = b""
    offset = len(header) + 16 * len(images)
    for size, png in images:
        side = 0 if size >= 256 else size  # 0 signifie 256 dans le format ICO
        directory += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
    return header + directory + b"".join(png for _, png in images)


def main() -> None:
    _OUTPUT.write_bytes(build_ico())
    print(f"{_OUTPUT} ({_OUTPUT.stat().st_size} octets, tailles {APP_ICON_SIZES})")


if __name__ == "__main__":
    main()
