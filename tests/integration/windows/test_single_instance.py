"""Deux processus réels : le second doit détecter le mutex et transmettre sa commande."""

from __future__ import annotations

import subprocess
import sys
import time

from nexusdesk.integrations.windows.single_instance import (
    OPEN_MAIN_WINDOW,
    SingleInstanceGuard,
    send_command,
)

_SERVER_SCRIPT = """
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import time
from PySide6.QtCore import QCoreApplication
from nexusdesk.integrations.windows.single_instance import SingleInstanceGuard, CommandServer

app = QCoreApplication([])

guard = SingleInstanceGuard()
assert guard.acquire(), "le mutex aurait du etre libre pour ce process"

received = []
server = CommandServer()
server.command_received.connect(received.append)
server.start()

deadline = time.monotonic() + 10
while time.monotonic() < deadline and not received:
    app.processEvents()
    time.sleep(0.05)

if received:
    print("RECEIVED:" + received[0], flush=True)

server.stop(2.0)
guard.release()
"""


def test_second_instance_detects_mutex_and_delivers_command() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", _SERVER_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        # Attend que le processus enfant ait acquis le mutex, en sondant plutôt qu'avec un
        # délai fixe (le démarrage de l'enfant — import de PySide6/SQLAlchemy — n'a pas une
        # durée garantie, surtout sous instrumentation de couverture).
        deadline = time.monotonic() + 10
        mutex_held_by_child = False
        while time.monotonic() < deadline:
            guard = SingleInstanceGuard()
            acquired = guard.acquire()
            guard.release()
            if not acquired:
                mutex_held_by_child = True
                break
            time.sleep(0.1)
        assert mutex_held_by_child, "le processus enfant n'a jamais acquis le mutex"

        delivered = send_command(OPEN_MAIN_WINDOW, timeout_ms=5000)
        assert delivered is True

        stdout, _ = process.communicate(timeout=10)
        assert f"RECEIVED:{OPEN_MAIN_WINDOW}" in stdout
        assert process.returncode == 0
    finally:
        if process.poll() is None:
            process.kill()
