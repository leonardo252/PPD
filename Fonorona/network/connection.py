from __future__ import annotations

import socket
import threading
from typing import Callable


MessageCallback = Callable[[str], None]
DisconnectCallback = Callable[[], None]


class StreamingConnection:
    """
    Gerencia uma conexão TCP persistente e bidirecional.

    A mesma conexão permanece aberta para enviar e receber
    várias mensagens durante toda a execução.
    """

    BUFFER_SIZE = 4096
    ENCODING = "utf-8"
    MESSAGE_SEPARATOR = "\n"

    def __init__(self, connection_socket: socket.socket) -> None:
        self._socket = connection_socket
        self._running = False

        self._receive_thread: threading.Thread | None = None
        self._send_lock = threading.Lock()

        self.on_message: MessageCallback | None = None
        self.on_disconnect: DisconnectCallback | None = None

    @property
    def is_connected(self) -> bool:
        return self._running

    def start_receiving(self) -> None:
        """
        Inicia uma thread responsável por receber mensagens.

        A thread de recebimento permite que o programa continue
        disponível para enviar mensagens ao mesmo tempo.
        """
        if self._running:
            return

        self._running = True

        self._receive_thread = threading.Thread(
            target=self._receive_loop,
            name="streaming-receive-thread",
            daemon=True,
        )
        self._receive_thread.start()

    def _receive_loop(self) -> None:
        """
        Mantém a leitura do socket ativa enquanto a conexão existir.
        """
        pending_data = ""

        try:
            while self._running:
                received_data = self._socket.recv(self.BUFFER_SIZE)

                if not received_data:
                    print("\nO outro participante encerrou a conexão.")
                    break

                pending_data += received_data.decode(self.ENCODING)

                while self.MESSAGE_SEPARATOR in pending_data:
                    message, pending_data = pending_data.split(
                        self.MESSAGE_SEPARATOR,
                        1,
                    )

                    if message and self.on_message is not None:
                        self.on_message(message)

        except ConnectionResetError:
            print("\nA conexão foi interrompida pelo outro participante.")

        except OSError as error:
            if self._running:
                print(f"\nErro ao receber mensagem: {error}")

        finally:
            self.close()

    def send(self, message: str) -> bool:
        """
        Envia uma mensagem sem fechar a conexão.

        O caractere de nova linha marca o final de cada mensagem.
        """
        if not self._running:
            print("Não existe uma conexão ativa.")
            return False

        normalized_message = message.replace(
            self.MESSAGE_SEPARATOR,
            " ",
        )

        encoded_message = (
            normalized_message + self.MESSAGE_SEPARATOR
        ).encode(self.ENCODING)

        try:
            # Evita que duas threads escrevam no socket simultaneamente.
            with self._send_lock:
                self._socket.sendall(encoded_message)

            return True

        except OSError as error:
            print(f"Erro ao enviar mensagem: {error}")
            self.close()
            return False

    def close(self) -> None:
        """
        Encerra a conexão de maneira segura.
        """
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

        if was_running and self.on_disconnect is not None:
            self.on_disconnect()