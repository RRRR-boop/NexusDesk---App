# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller : empaquetage en mode dossier (jamais --onefile, section 18)."""

import re
import tomllib
from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

project_root = Path(SPECPATH)
src_dir = project_root / "src"
migrations_dir = src_dir / "nexusdesk" / "database" / "migrations"
icons_dir = src_dir / "nexusdesk" / "resources" / "icons"

datas = []
for path in migrations_dir.rglob("*"):
    if path.is_file():
        relative_dir = path.relative_to(src_dir).parent
        datas.append((str(path), str(relative_dir)))
for path in icons_dir.glob("*.svg"):
    relative_dir = path.relative_to(src_dir).parent
    datas.append((str(path), str(relative_dir)))

# Modules Qt inutiles exclus pour rester sous l'objectif de 150 Mo installes (section 18).
excluded_qt_modules = [
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtCharts",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuick3D",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtBluetooth",
    "PySide6.QtSerialPort",
    "PySide6.QtSensors",
    "PySide6.QtPositioning",
    "PySide6.QtLocation",
    "PySide6.QtWebSockets",
    "PySide6.QtWebChannel",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtTest",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtStateMachine",
]

a = Analysis(
    [str(src_dir / "nexusdesk" / "__main__.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    # pywin32 importe win32timezone à l'exécution (dates renvoyées par
    # GetFileInformationByHandle, utilisé pour les liens physiques) : invisible pour
    # l'analyse statique de PyInstaller, d'où « No module named 'win32timezone' » sans lui.
    hiddenimports=["win32timezone"],
    excludes=excluded_qt_modules,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# Ressource de version Windows (Propriétés > Détails de NexusDesk.exe), dérivée de
# pyproject.toml : 0.2.1b2 -> FileVersion 0.2.1.0, ProductVersion « 0.2.1-beta.2 ».
_project = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
_pep440 = _project["version"]
_match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?", _pep440)
if _match is None:
    raise ValueError(f"Version non reconnue dans pyproject.toml : {_pep440}")
_numeric = tuple(int(part) for part in _match.groups()[:3]) + (0,)
_label = {"a": "alpha", "b": "beta", "rc": "rc"}.get(_match.group(4) or "")
_display_version = ".".join(_match.groups()[:3]) + (f"-{_label}.{_match.group(5)}" if _label else "")
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=_numeric, prodvers=_numeric),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040C04B0",  # français (France), Unicode
                    [
                        StringStruct("CompanyName", "NexusDesk"),
                        StringStruct("FileDescription", "NexusDesk - boîte à outils Windows"),
                        StringStruct("FileVersion", _display_version),
                        StringStruct("InternalName", "NexusDesk"),
                        StringStruct("LegalCopyright", "Licence GNU GPL v3 (GPL-3.0-only)"),
                        StringStruct("OriginalFilename", "NexusDesk.exe"),
                        StringStruct("ProductName", "NexusDesk"),
                        StringStruct("ProductVersion", _display_version),
                        StringStruct("Comments", "Logiciel libre : https://github.com/RRRR-boop/NexusDesk---App"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [0x040C, 1200])]),
    ],
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NexusDesk",
    console=False,
    version=version_info,
    icon=str(icons_dir / "app.ico"),  # généré par scripts/make_icon.py
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="NexusDesk",
)
