from __future__ import annotations

import json
import socket
import threading
from typing import Any, Callable, Dict, Optional


MessageCallback = Callable[[Dict[str, Any]], None]
DisconnectCallback = Callable[[], None]


class StreamingConnection:
    """
    Conexão TCP persistente.

    Cada mensagem é um JSON terminado por quebra de linha. O socket
    permanece aberto para várias mensagens nos dois sentidos.
    """

    BUFFER_SIZE = 4096
    ENCODING = "utf-8"
    MESSAGE_SEPARATOR = "\n"

    def __init__(self, connection_socket: socket.socket) -> None:
        self._socket = connection_socket
        self._running = False
        self._receive_thread: Optional[threading.Thread] = None
        self._send_lock = threading.Lock()

        self.on_message: Optional[MessageCallback] = None
        self.on_disconnect: Optional[DisconnectCallback] = None

    @property
    def is_connected(self) -> bool:
        return self._running

    def start_receiving(self) -> None:
        if self._running:
            return

        self._running = True
        self._receive_thread = threading.Thread(
            target=self._receive_loop,
            daemon=True,
            name="stream-receiver",
        )
        self._receive_thread.start()

    def send(self, message: Dict[str, Any]) -> bool:
        if not self._running:
            return False

        try:
            payload = json.dumps(
                message,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            encoded = (
                payload + self.MESSAGE_SEPARATOR
            ).encode(self.ENCODING)

            with self._send_lock:
                self._socket.sendall(encoded)

            return True

        except (OSError, TypeError, ValueError):
            self.close()
            return False

    def _receive_loop(self) -> None:
        pending = ""

        try:
            while self._running:
                chunk = self._socket.recv(self.BUFFER_SIZE)

                if not chunk:
                    break

                pending += chunk.decode(self.ENCODING)

                while self.MESSAGE_SEPARATOR in pending:
                    raw_message, pending = pending.split(
                        self.MESSAGE_SEPARATOR,
                        1,
                    )

                    if not raw_message:
                        continue

                    try:
                        message = json.loads(raw_message)
                    except json.JSONDecodeError:
                        continue

                    if isinstance(message, dict) and self.on_message:
                        self.on_message(message)

        except (ConnectionResetError, UnicodeDecodeError, OSError):
            pass

        finally:
            self.close()

    def close(self) -> None:
        was_running = self._running
        self._running = False

        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self._socket.close()
        except OSError:
            pass

        if was_running and self.on_disconnect:
            self.on_disconnect()
