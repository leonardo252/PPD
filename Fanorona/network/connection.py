import json
import socket
import threading


class JsonConnection:
    """Conexao TCP persistente com uma mensagem JSON por linha."""

    def __init__(self, sock, on_message, on_disconnect):
        self.sock = sock
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.running = True
        self.send_lock = threading.Lock()

    def start(self):
        threading.Thread(target=self._receive_loop, daemon=True).start()

    def send(self, payload):
        if not self.running:
            return False
        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            with self.send_lock:
                self.sock.sendall(data)
            return True
        except OSError:
            self.close()
            return False

    def _receive_loop(self):
        pending = ""
        try:
            while self.running:
                data = self.sock.recv(4096)
                if not data:
                    break
                pending += data.decode("utf-8")
                while "\n" in pending:
                    line, pending = pending.split("\n", 1)
                    if line:
                        try:
                            self.on_message(json.loads(line))
                        except (json.JSONDecodeError, TypeError):
                            continue
        except (OSError, UnicodeDecodeError):
            pass
        finally:
            self.close()

    def close(self):
        if not self.running:
            return
        self.running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()
        self.on_disconnect()
