"""Instance unique (mutex nommé) et relais de commandes par tube nommé (ADR-0002).

Un seul processus NexusDesk tourne à la fois (mutex ``Local\\NexusDesk``). Un second
lancement transmet sa demande à l'instance existante via un tube nommé dont la DACL est
restreinte au SID de l'utilisateur courant, puis se termine rapidement sans jamais créer de
``QApplication``.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

import win32api
import win32con
import win32event
import win32file
import win32pipe
import win32security
import winerror
from PySide6.QtCore import QObject, Signal

_logger = logging.getLogger("nexusdesk.integrations.single_instance")

_MUTEX_NAME = "Local\\NexusDesk"
_PIPE_NAME = r"\\.\pipe\NexusDesk"
_BUFFER_SIZE = 4096

OPEN_MAIN_WINDOW = "OPEN_MAIN_WINDOW"
# QUIT : réservé aux tests (ADR-0009), voir app.py pour le garde par variable d'environnement.
QUIT = "QUIT"
_STOP_SERVER_SENTINEL = "__STOP_SERVER__"  # usage interne, pour débloquer proprement le serveur


class SingleInstanceGuard:
    """Tient le mutex nommé pendant toute la durée de vie du processus."""

    def __init__(self) -> None:
        self._handle: Any = None

    def acquire(self) -> bool:
        """Renvoie True si cette instance est la première à démarrer.

        Le handle est conservé en attribut d'instance : s'il n'était stocké que dans une
        variable locale, le ramasse-miettes le refermerait et libérerait silencieusement le
        mutex, rendant l'instance unique intermittente.
        """
        # Les stubs typent le 1er paramètre comme obligatoire ; None est accepté à l'exécution.
        handle = win32event.CreateMutex(None, False, _MUTEX_NAME)  # type: ignore[arg-type]
        self._handle = handle
        already_running = win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS
        return not already_running

    def release(self) -> None:
        if self._handle is not None:
            win32api.CloseHandle(self._handle)
            self._handle = None


def _current_user_security_attributes() -> Any:
    """DACL restreinte au SID de l'utilisateur courant (pas d'accès inter-utilisateurs)."""
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    user_sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
    acl = win32security.ACL()
    acl.AddAccessAllowedAce(
        win32security.ACL_REVISION, win32con.GENERIC_READ | win32con.GENERIC_WRITE, user_sid
    )
    security_descriptor = win32security.SECURITY_DESCRIPTOR()
    security_descriptor.SetSecurityDescriptorDacl(1, acl, 0)
    security_attributes = win32security.SECURITY_ATTRIBUTES()
    security_attributes.SECURITY_DESCRIPTOR = security_descriptor
    return security_attributes


def send_command(command: str, timeout_ms: int = 2000) -> bool:
    """Envoie une commande à l'instance existante. Renvoie False si personne n'écoute."""
    try:
        win32pipe.WaitNamedPipe(_PIPE_NAME, timeout_ms)
        handle = win32file.CreateFile(
            _PIPE_NAME,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0,
            None,
            win32con.OPEN_EXISTING,
            0,
            None,
        )
    except Exception:
        _logger.info("Aucune instance NexusDesk à l'écoute sur le tube nommé.")
        return False

    # Les stubs typent les handles retournés (PyHANDLE) comme incompatibles avec les
    # paramètres "int" déclarés ailleurs ; limitation connue des stubs, pas une vraie erreur.
    try:
        win32file.WriteFile(handle, command.encode("utf-8"))  # type: ignore[arg-type]
        win32file.ReadFile(handle, _BUFFER_SIZE)  # type: ignore[call-overload]
    finally:
        win32file.CloseHandle(handle)  # type: ignore[arg-type]
    return True


class CommandServer(QObject):
    """Écoute le tube nommé côté instance primaire et republie les commandes reçues."""

    command_received = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._serve_forever, daemon=True, name="nexusdesk-ipc-server"
        )
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        if not self._running:
            return
        self._running = False
        send_command(_STOP_SERVER_SENTINEL, timeout_ms=1000)
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _serve_forever(self) -> None:
        while self._running:
            try:
                handle = win32pipe.CreateNamedPipe(
                    _PIPE_NAME,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE
                    | win32pipe.PIPE_READMODE_MESSAGE
                    | win32pipe.PIPE_WAIT,
                    1,
                    _BUFFER_SIZE,
                    _BUFFER_SIZE,
                    0,
                    _current_user_security_attributes(),
                )
            except Exception:
                _logger.exception("Impossible de créer le tube nommé NexusDesk.")
                return

            try:
                win32pipe.ConnectNamedPipe(handle, None)
                _, data = win32file.ReadFile(handle, _BUFFER_SIZE)
                command = data.decode("utf-8")
                win32file.WriteFile(handle, b"ACK")
                win32file.FlushFileBuffers(handle)
            except Exception:
                _logger.exception("Erreur sur le tube nommé NexusDesk.")
                continue
            finally:
                win32pipe.DisconnectNamedPipe(handle)
                win32file.CloseHandle(handle)

            if command == _STOP_SERVER_SENTINEL:
                break
            self.command_received.emit(command)
