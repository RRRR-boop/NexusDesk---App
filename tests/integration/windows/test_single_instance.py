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
        time.sleep(1.0)  # laisse le processus enfant acquérir le mutex et démarrer le tube

        guard = SingleInstanceGuard()
        assert guard.acquire() is False  # le process enfant détient déjà le mutex
        guard.release()

        delivered = send_command(OPEN_MAIN_WINDOW, timeout_ms=5000)
        assert delivered is True

        stdout, _ = process.communicate(timeout=10)
        assert f"RECEIVED:{OPEN_MAIN_WINDOW}" in stdout
        assert process.returncode == 0
    finally:
        if process.poll() is None:
            process.kill()
