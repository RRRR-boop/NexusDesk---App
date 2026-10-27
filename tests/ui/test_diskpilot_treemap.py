from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from nexusdesk.models.diskpilot_domain import FileNode, FolderNode
from nexusdesk.ui.pages.diskpilot.treemap_widget import TreemapWidget
from nexusdesk.ui.theme.tokens import DARK_COLORS


def _build_widget(qtbot: Any, folder: FolderNode | None) -> TreemapWidget:
    widget = TreemapWidget()
    widget.resize(240, 160)
    widget.set_folder(folder, DARK_COLORS)
    qtbot.addWidget(widget)
    return widget


def test_double_click_on_single_child_folder_emits_folder_opened(qtbot: Any) -> None:
    child = FolderNode(path=Path(r"C:\root\sous_dossier"), depth=1, logical_size=100)
    root = FolderNode(path=Path(r"C:\root"), depth=0, children=[child], logical_size=100)
    widget = _build_widget(qtbot, root)

    opened: list[object] = []
    widget.folder_opened.connect(opened.append)

    center = QPoint(widget.width() // 2, widget.height() // 2)
    QTest.mouseDClick(widget, Qt.MouseButton.LeftButton, pos=center)

    assert opened == [child]


def test_double_click_on_a_file_does_not_emit_folder_opened(qtbot: Any) -> None:
    file_node = FileNode(
        path=Path(r"C:\root\fichier.txt"),
        logical_size=100,
        size_on_disk=100,
        modified_at=datetime(2026, 1, 1),
        category="documents",
    )
    root = FolderNode(path=Path(r"C:\root"), depth=0, files=[file_node], logical_size=100)
    widget = _build_widget(qtbot, root)

    opened: list[object] = []
    widget.folder_opened.connect(opened.append)

    center = QPoint(widget.width() // 2, widget.height() // 2)
    QTest.mouseDClick(widget, Qt.MouseButton.LeftButton, pos=center)

    assert opened == []


def test_double_click_with_no_folder_set_does_not_crash(qtbot: Any) -> None:
    widget = _build_widget(qtbot, None)

    opened: list[object] = []
    widget.folder_opened.connect(opened.append)

    QTest.mouseDClick(
        widget, Qt.MouseButton.LeftButton, pos=QPoint(widget.width() // 2, widget.height() // 2)
    )

    assert opened == []


def test_resize_recomputes_layout_without_crashing(qtbot: Any) -> None:
    # resizeEvent n'est dispatche par Qt que pour un widget reellement affiche : un simple
    # .resize() sur un widget jamais montre ne declenche pas le recalcul (constate
    # empiriquement), d'ou le show()/waitExposed() explicite ici.
    child = FolderNode(path=Path(r"C:\root\sous_dossier"), depth=1, logical_size=100)
    root = FolderNode(path=Path(r"C:\root"), depth=0, children=[child], logical_size=100)
    widget = _build_widget(qtbot, root)
    widget.show()
    qtbot.waitExposed(widget)

    widget.resize(500, 50)
    qtbot.wait(50)

    opened: list[object] = []
    widget.folder_opened.connect(opened.append)
    QTest.mouseDClick(
        widget, Qt.MouseButton.LeftButton, pos=QPoint(widget.width() // 2, widget.height() // 2)
    )

    assert opened == [child]
