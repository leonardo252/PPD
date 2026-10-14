import secrets
import threading
import time

try:
    import Pyro5.api
except ImportError:  # Permite testar a logica antes de instalar a dependencia.
    Pyro5 = None

from game.board import BLACK, WHITE
from game.game import FanoronaGame, InvalidMove


def _expose(cls):
    if Pyro5 is None:
        return cls
    return Pyro5.api.expose(cls)


@_expose
class FanoronaService:
    """Objeto remoto autoritativo: toda alteracao da partida ocorre aqui."""

    def __init__(self):
        self.game = FanoronaGame()
        self.lock = threading.RLock()
        self.players = {}
        self.color_tokens = {}
        self.messages = []
        self.state_version = 0
        self.next_message_id = 1

    def ping(self):
        return {"success": True, "server_time": time.time()}

    def join_game(self, player_name):
        with self.lock:
            name = str(player_name).strip()[:30] or "Jogador"
            if len(self.players) >= 2:
                return self._error("A partida ja possui dois jogadores.")

            color = WHITE if WHITE not in self.color_tokens else BLACK
            token = secrets.token_urlsafe(24)
            self.players[token] = {"name": name, "color": color}
            self.color_tokens[color] = token
            self.state_version += 1
            return {
                "success": True,
                "token": token,
                "color": color,
                "snapshot": self._snapshot(),
            }

    def get_snapshot(self, token, known_version=-1):
        with self.lock:
            self._require_player(token)
            if int(known_version) == self.state_version:
                return {"success": True, "changed": False, "version": self.state_version}
            return {"success": True, "changed": True, "snapshot": self._snapshot()}

    def make_move(self, token, origin, destination, capture_type=None):
        with self.lock:
            player = self._require_player(token)
            if not self._game_started():
                return self._error("Aguardando o segundo jogador.")
            if self.game.turn != player["color"]:
                return self._error("Nao e o seu turno.")
            try:
                captured = self.game.move(origin, destination, capture_type)
            except (InvalidMove, TypeError, IndexError) as error:
                return self._error(str(error))
            self.state_version += 1
            return {
                "success": True,
                "captured": [list(position) for position in captured],
                "snapshot": self._snapshot(),
            }

    def end_capture_sequence(self, token):
        with self.lock:
            player = self._require_player(token)
            if self.game.turn != player["color"]:
                return self._error("Nao e o seu turno.")
            if self.game.chain_position is None:
                return self._error("Nao existe sequencia de captura ativa.")
            self.game.end_turn()
            self.state_version += 1
            return {"success": True, "snapshot": self._snapshot()}

    def send_chat(self, token, text):
        with self.lock:
            player = self._require_player(token)
            text = str(text).strip()
            if not text:
                return self._error("A mensagem esta vazia.")
            message = {
                "id": self.next_message_id,
                "author": player["name"],
                "color": player["color"],
                "text": text[:500],
            }
            self.next_message_id += 1
            self.messages.append(message)
            return {"success": True, "message": message}

    def get_messages(self, token, after_id=0):
        with self.lock:
            self._require_player(token)
            after_id = int(after_id)
            return {
                "success": True,
                "messages": [message.copy() for message in self.messages if message["id"] > after_id],
            }

    def surrender(self, token):
        with self.lock:
            player = self._require_player(token)
            if self.game.winner:
                return self._error("A partida ja terminou.")
            self.game.surrender(player["color"])
            self.state_version += 1
            return {"success": True, "snapshot": self._snapshot()}

    def leave_game(self, token):
        with self.lock:
            was_started = self._game_started()
            player = self.players.pop(token, None)
            if player is None:
                return {"success": True}
            self.color_tokens.pop(player["color"], None)
            if was_started and not self.game.winner:
                self.game.surrender(player["color"])
            self.state_version += 1
            return {"success": True}

    def _game_started(self):
        return WHITE in self.color_tokens and BLACK in self.color_tokens

    def _require_player(self, token):
        player = self.players.get(str(token))
        if player is None:
            raise ValueError("Jogador nao autorizado.")
        return player

    def _snapshot(self):
        players = {
            data["color"]: data["name"]
            for data in self.players.values()
        }
        return {
            "version": self.state_version,
            "started": self._game_started(),
            "players": players,
            "game": self.game.state(),
        }

    @staticmethod
    def _error(message):
        return {"success": False, "error": str(message)}
