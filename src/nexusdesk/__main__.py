"""Point d'entrée : instance unique, puis boucle Qt (section 4)."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from nexusdesk.app import Application
from nexusdesk.integrations.windows.single_instance import (
    OPEN_MAIN_WINDOW,
    SingleInstanceGuard,
    send_command,
)


def main() -> int:
    dev_mode = "-Dev" in sys.argv or "--dev" in sys.argv

    guard = SingleInstanceGuard()
    if not guard.acquire():
        # Une instance tourne déjà : on lui transmet la demande et on sort rapidement,
        # avant de créer un QApplication inutile (section 4).
        send_command(OPEN_MAIN_WINDOW)
        return 0

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    _application = Application(qt_app, dev_mode=dev_mode)
    _application.main_window.show()

    exit_code = qt_app.exec()
    guard.release()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
