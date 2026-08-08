from __future__ import annotations

import math
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Any, Dict, List, Optional, Tuple

from game.board import COLUMNS, ROWS
from game.game import FanoronaGame
from game.models import CaptureType, Move, Player, Position
from network.connection import StreamingConnection


class FanoronaNetworkWindow:
    PIECE_RADIUS = 17

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.game = FanoronaGame()

        self.connection: Optional[StreamingConnection] = None
        self.server_socket: Optional[socket.socket] = None
        self.connection_mode: Optional[str] = None
        self.local_player: Optional[Player] = None

        self.selected: Optional[Position] = None
        self.valid_destinations: List[Position] = []

        self.mode_var = tk.StringVar(value="server")
        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="5000")
        self.status_var = tk.StringVar(value="Desconectado")
        self.turn_var = tk.StringVar(value="Conecte os jogadores para iniciar.")
        self.count_var = tk.StringVar()

        self.root.title("Fanorona em Rede")
        self.root.geometry("1180x760")
        self.root.minsize(980, 680)
        self.root.protocol("WM_DELETE_WINDOW", self._close_window)

        self._build_ui()
        self._update_mode()
        self._refresh()

    def _build_ui(self) -> None:
        connection_frame = tk.LabelFrame(
            self.root,
            text="Conexão",
            padx=10,
            pady=10,
        )
        connection_frame.pack(fill=tk.X, padx=12, pady=(12, 6))

        tk.Radiobutton(
            connection_frame,
            text="Servidor (Brancas)",
            variable=self.mode_var,
            value="server",
            command=self._update_mode,
        ).grid(row=0, column=0, padx=5)

        tk.Radiobutton(
            connection_frame,
            text="Cliente (Pretas)",
            variable=self.mode_var,
            value="client",
            command=self._update_mode,
        ).grid(row=0, column=1, padx=5)

        tk.Label(connection_frame, text="IP:").grid(row=0, column=2, padx=(18, 4))

        self.host_entry = tk.Entry(
            connection_frame,
            textvariable=self.host_var,
            width=16,
        )
        self.host_entry.grid(row=0, column=3, padx=4)

        tk.Label(connection_frame, text="Porta:").grid(row=0, column=4, padx=(12, 4))

        self.port_entry = tk.Entry(
            connection_frame,
            textvariable=self.port_var,
            width=7,
        )
        self.port_entry.grid(row=0, column=5, padx=4)

        self.connect_button = tk.Button(
            connection_frame,
            text="Iniciar servidor",
            command=self._connection_action,
            width=16,
        )
        self.connect_button.grid(row=0, column=6, padx=(14, 4))

        tk.Label(
            connection_frame,
            textvariable=self.status_var,
            anchor="w",
        ).grid(row=1, column=0, columnspan=7, sticky="ew", pady=(8, 0))

        body = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            sashwidth=6,
        )
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        game_frame = tk.Frame(body)
        side_frame = tk.Frame(body, width=300)
        body.add(game_frame, stretch="always")
        body.add(side_frame)

        self.canvas = tk.Canvas(
            game_frame,
            background="#d9b77e",
            highlightbackground="#5c4328",
            highlightthickness=1,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_board_click)
        self.canvas.bind("<Configure>", lambda _: self._refresh())

        info_frame = tk.LabelFrame(
            side_frame,
            text="Partida",
            padx=10,
            pady=10,
        )
        info_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            info_frame,
            textvariable=self.turn_var,
            wraplength=260,
            justify=tk.LEFT,
            font=("Arial", 11, "bold"),
        ).pack(fill=tk.X)

        tk.Label(
            info_frame,
            textvariable=self.count_var,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(8, 0))

        self.finish_button = tk.Button(
            info_frame,
            text="Encerrar sequência",
            command=self._request_finish_chain,
            state=tk.DISABLED,
        )
        self.finish_button.pack(fill=tk.X, pady=(10, 4))

        self.surrender_button = tk.Button(
            info_frame,
            text="Desistir",
            command=self._request_surrender,
            state=tk.DISABLED,
        )
        self.surrender_button.pack(fill=tk.X)

        chat_frame = tk.LabelFrame(
            side_frame,
            text="Chat",
            padx=8,
            pady=8,
        )
        chat_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_history = scrolledtext.ScrolledText(
            chat_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            width=32,
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)

        message_frame = tk.Frame(chat_frame)
        message_frame.pack(fill=tk.X, pady=(8, 0))

        self.chat_entry = tk.Entry(
            message_frame,
            state=tk.DISABLED,
        )
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_entry.bind("<Return>", lambda _: self._send_chat())

        self.chat_button = tk.Button(
            message_frame,
            text="Enviar",
            command=self._send_chat,
            state=tk.DISABLED,
        )
        self.chat_button.pack(side=tk.LEFT, padx=(6, 0))

    def _update_mode(self) -> None:
        if self.connection is not None:
            return

        if self.mode_var.get() == "server":
            self.host_entry.configure(state=tk.DISABLED)
            self.connect_button.configure(text="Iniciar servidor")
        else:
            self.host_entry.configure(state=tk.NORMAL)
            self.connect_button.configure(text="Conectar")

    def _connection_action(self) -> None:
        if self.connection is not None or self.server_socket is not None:
            self._disconnect()
            return

        try:
            port = int(self.port_var.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Informe uma porta entre 1 e 65535.")
            return

        self._set_connection_controls(False)
        self.connect_button.configure(text="Desconectar", state=tk.NORMAL)

        if self.mode_var.get() == "server":
            self.connection_mode = "server"
            self.local_player = Player.WHITE
            self.status_var.set("Iniciando servidor...")
            threading.Thread(
                target=self._server_worker,
                args=(port,),
                daemon=True,
            ).start()
        else:
            host = self.host_var.get().strip()

            if not host:
                messagebox.showerror("Erro", "Informe o IP do servidor.")
                self._restore_connection_controls()
                return

            self.connection_mode = "client"
            self.local_player = Player.BLACK
            self.status_var.set("Conectando a {}:{}...".format(host, port))
            threading.Thread(
                target=self._client_worker,
                args=(host, port),
                daemon=True,
            ).start()

    def _server_worker(self, port: int) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind(("0.0.0.0", port))
            server.listen(1)
            self.server_socket = server

            local_ip = self._local_ip()
            self.root.after(
                0,
                lambda: self.status_var.set(
                    "Aguardando cliente em {}:{}".format(local_ip, port)
                ),
            )

            client_socket, address = server.accept()
            self.root.after(
                0,
                lambda: self._establish_connection(
                    client_socket,
                    "Cliente conectado: {}:{}".format(
                        address[0],
                        address[1],
                    ),
                ),
            )

        except OSError as error:
            self.root.after(
                0,
                lambda error=error: self._connection_error(str(error)),
            )
        finally:
            try:
                server.close()
            except OSError:
                pass
            self.server_socket = None

    def _client_worker(self, host: str, port: int) -> None:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)

        try:
            client.connect((host, port))
            client.settimeout(None)
            self.root.after(
                0,
                lambda: self._establish_connection(
                    client,
                    "Conectado ao servidor {}:{}.".format(host, port),
                ),
            )
        except OSError as error:
            try:
                client.close()
            except OSError:
                pass
            self.root.after(
                0,
                lambda error=error: self._connection_error(str(error)),
            )

    def _establish_connection(
        self,
        socket_connection: socket.socket,
        message: str,
    ) -> None:
        self.connection = StreamingConnection(socket_connection)
        self.connection.on_message = self._on_network_message
        self.connection.on_disconnect = self._on_network_disconnect
        self.connection.start_receiving()

        self.status_var.set(message)
        self.chat_entry.configure(state=tk.NORMAL)
        self.chat_button.configure(state=tk.NORMAL)
        self.surrender_button.configure(state=tk.NORMAL)
        self._append_system(message)

        if self.connection_mode == "server":
            self.game.reset()
            self._broadcast_state("Partida iniciada.")
        else:
            self.connection.send({"type": "ready"})

        self._refresh()

    def _on_network_message(self, message: Dict[str, Any]) -> None:
        self.root.after(
            0,
            lambda: self._handle_network_message(message),
        )

    def _handle_network_message(self, message: Dict[str, Any]) -> None:
        message_type = message.get("type")

        if message_type == "ready" and self.connection_mode == "server":
            self._broadcast_state("Jogador cliente pronto.")
            return

        if message_type == "chat":
            sender = message.get("sender", "Jogador")
            text = str(message.get("message", ""))
            self._append_chat(sender, text)
            return

        if message_type == "state":
            if self.connection_mode == "client":
                self.game.load_serialized(message["game"])
                self.selected = None
                self.valid_destinations = []
                self._append_system(str(message.get("message", "Estado atualizado.")))
                self._refresh()

                if self.game.winner:
                    messagebox.showinfo(
                        "Fim da partida",
                        "{} venceu.".format(
                            self._player_name(self.game.winner)
                        ),
                    )
            return

        if message_type == "move_request" and self.connection_mode == "server":
            self._server_process_move(message)
            return

        if message_type == "finish_chain_request" and self.connection_mode == "server":
            self._server_finish_chain(message)
            return

        if message_type == "surrender_request" and self.connection_mode == "server":
            self._server_surrender(message)
            return

        if message_type == "error":
            messagebox.showwarning(
                "Ação recusada",
                str(message.get("message", "Ação inválida.")),
            )

    def _server_process_move(self, message: Dict[str, Any]) -> None:
        try:
            requested_player = Player(message["player"])

            if requested_player is not self.game.current_player:
                self._send_error("Não é o turno desse jogador.")
                return

            origin = tuple(message["origin"])
            destination = tuple(message["destination"])

            capture_value = message.get("capture_type")
            capture_type = (
                CaptureType(capture_value)
                if capture_value
                else None
            )

            result = self.game.play(
                Move(origin, destination, capture_type)
            )

            if not result.success:
                self._send_error(result.message)
                return

            self._broadcast_state(result.message)

            if result.winner:
                messagebox.showinfo(
                    "Fim da partida",
                    "{} venceu.".format(
                        self._player_name(result.winner)
                    ),
                )

        except (KeyError, ValueError, TypeError):
            self._send_error("Mensagem de jogada inválida.")

    def _server_finish_chain(self, message: Dict[str, Any]) -> None:
        try:
            requested_player = Player(message["player"])

            if requested_player is not self.game.current_player:
                self._send_error("Não é o turno desse jogador.")
                return

            result = self.game.finish_capture_chain()

            if not result.success:
                self._send_error(result.message)
                return

            self._broadcast_state(result.message)
        except (KeyError, ValueError):
            self._send_error("Solicitação inválida.")

    def _server_surrender(self, message: Dict[str, Any]) -> None:
        try:
            player = Player(message["player"])
            result = self.game.surrender(player)
            self._broadcast_state(result.message)

            if result.winner:
                messagebox.showinfo(
                    "Fim da partida",
                    "{} venceu por desistência.".format(
                        self._player_name(result.winner)
                    ),
                )
        except (KeyError, ValueError):
            self._send_error("Solicitação inválida.")

    def _request_move(
        self,
        origin: Position,
        destination: Position,
        capture_type: Optional[CaptureType],
    ) -> None:
        if self.local_player is None:
            return

        message = {
            "type": "move_request",
            "player": self.local_player.value,
            "origin": list(origin),
            "destination": list(destination),
            "capture_type": capture_type.value if capture_type else None,
        }

        if self.connection_mode == "server":
            self._server_process_move(message)
        elif self.connection:
            self.connection.send(message)

    def _request_finish_chain(self) -> None:
        if self.local_player is None:
            return

        message = {
            "type": "finish_chain_request",
            "player": self.local_player.value,
        }

        if self.connection_mode == "server":
            self._server_finish_chain(message)
        elif self.connection:
            self.connection.send(message)

    def _request_surrender(self) -> None:
        if self.local_player is None:
            return

        if not messagebox.askyesno(
            "Desistir",
            "Deseja realmente desistir?",
        ):
            return

        message = {
            "type": "surrender_request",
            "player": self.local_player.value,
        }

        if self.connection_mode == "server":
            self._server_surrender(message)
        elif self.connection:
            self.connection.send(message)

    def _broadcast_state(self, message: str) -> None:
        state_message = {
            "type": "state",
            "game": self.game.serialize(),
            "message": message,
        }

        if self.connection:
            self.connection.send(state_message)

        self.selected = None
        self.valid_destinations = []
        self._append_system(message)
        self._refresh()

    def _send_error(self, message: str) -> None:
        if self.connection:
            self.connection.send({
                "type": "error",
                "message": message,
            })

    def _on_board_click(self, event: tk.Event) -> None:
        if not self._can_local_player_move():
            return

        position = self._point_to_position(event.x, event.y)

        if position is None:
            return

        if self.selected is None:
            self._select_piece(position)
            return

        if position == self.selected:
            if not self.game.is_capture_chain:
                self.selected = None
                self.valid_destinations = []
                self._refresh()
            return

        if position in self.valid_destinations:
            self._choose_and_request_move(self.selected, position)
            return

        self._select_piece(position)

    def _select_piece(self, position: Position) -> None:
        if self.local_player is None:
            return

        if self.game.board.get(position) is not self.local_player:
            return

        if self.game.is_capture_chain and position != self.game.chain_piece:
            return

        destinations = self.game.legal_destinations(position)

        if destinations:
            self.selected = position
            self.valid_destinations = destinations
            self._refresh()

    def _choose_and_request_move(
        self,
        origin: Position,
        destination: Position,
    ) -> None:
        options = self.game.capture_options(origin, destination)
        capture_type: Optional[CaptureType] = None

        if len(options) == 1:
            capture_type = next(iter(options))

        elif len(options) == 2:
            capture_type = self._capture_dialog()

            if capture_type is None:
                return

        self._request_move(origin, destination, capture_type)

    def _capture_dialog(self) -> Optional[CaptureType]:
        answer = messagebox.askyesnocancel(
            "Tipo de captura",
            "Sim: aproximação\nNão: afastamento\nCancelar: não mover",
        )

        if answer is None:
            return None

        return (
            CaptureType.APPROACH
            if answer
            else CaptureType.WITHDRAWAL
        )

    def _send_chat(self) -> None:
        if not self.connection or self.local_player is None:
            return

        text = self.chat_entry.get().strip()

        if not text:
            return

        sender = self._player_name(self.local_player)
        message = {
            "type": "chat",
            "sender": sender,
            "message": text,
        }

        if self.connection.send(message):
            self._append_chat("Você", text)
            self.chat_entry.delete(0, tk.END)

    def _can_local_player_move(self) -> bool:
        return (
            self.connection is not None
            and self.local_player is not None
            and self.game.winner is None
            and self.game.current_player is self.local_player
        )

    def _refresh(self) -> None:
        self._draw_board()

        white_count = self.game.board.count(Player.WHITE)
        black_count = self.game.board.count(Player.BLACK)
        self.count_var.set(
            "Brancas: {}\nPretas: {}".format(
                white_count,
                black_count,
            )
        )

        if self.game.winner:
            self.turn_var.set(
                "Vencedor: {}".format(
                    self._player_name(self.game.winner)
                )
            )
            self.finish_button.configure(state=tk.DISABLED)
            return

        if self.connection is None:
            self.turn_var.set("Conecte os dois jogadores para iniciar.")
            self.finish_button.configure(state=tk.DISABLED)
            return

        local_name = (
            self._player_name(self.local_player)
            if self.local_player
            else "-"
        )
        current_name = self._player_name(self.game.current_player)

        text = "Você joga com {}.\nTurno atual: {}.".format(
            local_name,
            current_name,
        )

        if self.game.capture_is_required:
            text += "\nExiste uma captura obrigatória."

        if self.game.is_capture_chain:
            text += "\nSequência de captura em andamento."

        self.turn_var.set(text)

        can_finish = (
            self._can_local_player_move()
            and self.game.is_capture_chain
        )
        self.finish_button.configure(
            state=tk.NORMAL if can_finish else tk.DISABLED
        )

    def _draw_board(self) -> None:
        self.canvas.delete("all")
        drawn = set()

        for row in range(ROWS):
            for column in range(COLUMNS):
                origin = (row, column)
                x1, y1 = self._position_to_point(origin)

                for destination in self.game.board.neighbors(origin):
                    key = tuple(sorted((origin, destination)))

                    if key in drawn:
                        continue

                    drawn.add(key)
                    x2, y2 = self._position_to_point(destination)

                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill="#5c4328",
                        width=2,
                    )

        for destination in self.valid_destinations:
            x, y = self._position_to_point(destination)
            self.canvas.create_oval(
                x - 13, y - 13, x + 13, y + 13,
                fill="#6fbf73",
                outline="#27632b",
                width=2,
            )

        if self.selected:
            x, y = self._position_to_point(self.selected)
            self.canvas.create_oval(
                x - 25, y - 25, x + 25, y + 25,
                outline="#e8b923",
                width=4,
            )

        for row in range(ROWS):
            for column in range(COLUMNS):
                position = (row, column)
                x, y = self._position_to_point(position)

                self.canvas.create_oval(
                    x - 4, y - 4, x + 4, y + 4,
                    fill="#5c4328",
                    outline="",
                )

                player = self.game.board.get(position)

                if player is None:
                    continue

                fill = "#f4f1e8" if player is Player.WHITE else "#222222"

                self.canvas.create_oval(
                    x - self.PIECE_RADIUS,
                    y - self.PIECE_RADIUS,
                    x + self.PIECE_RADIUS,
                    y + self.PIECE_RADIUS,
                    fill=fill,
                    outline="#111111",
                    width=2,
                )

    def _position_to_point(
        self,
        position: Position,
    ) -> Tuple[float, float]:
        width = max(self.canvas.winfo_width(), 500)
        height = max(self.canvas.winfo_height(), 400)

        margin_x = 55
        margin_y = 65

        spacing_x = (width - 2 * margin_x) / (COLUMNS - 1)
        spacing_y = (height - 2 * margin_y) / (ROWS - 1)

        row, column = position

        return (
            margin_x + column * spacing_x,
            margin_y + row * spacing_y,
        )

    def _point_to_position(
        self,
        x: float,
        y: float,
    ) -> Optional[Position]:
        best: Optional[Position] = None
        best_distance = float("inf")

        for row in range(ROWS):
            for column in range(COLUMNS):
                px, py = self._position_to_point((row, column))
                distance = math.hypot(x - px, y - py)

                if distance < best_distance:
                    best_distance = distance
                    best = (row, column)

        return best if best_distance <= 30 else None

    def _append_chat(self, sender: str, text: str) -> None:
        self.chat_history.configure(state=tk.NORMAL)
        self.chat_history.insert(
            tk.END,
            "{}: {}\n".format(sender, text),
        )
        self.chat_history.configure(state=tk.DISABLED)
        self.chat_history.see(tk.END)

    def _append_system(self, text: str) -> None:
        self.chat_history.configure(state=tk.NORMAL)
        self.chat_history.insert(
            tk.END,
            "[Sistema] {}\n".format(text),
        )
        self.chat_history.configure(state=tk.DISABLED)
        self.chat_history.see(tk.END)

    def _disconnect(self) -> None:
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

        if self.connection:
            connection = self.connection
            self.connection = None
            connection.close()

        self.status_var.set("Desconectado")
        self.chat_entry.configure(state=tk.DISABLED)
        self.chat_button.configure(state=tk.DISABLED)
        self.surrender_button.configure(state=tk.DISABLED)
        self.local_player = None
        self.connection_mode = None
        self.selected = None
        self.valid_destinations = []
        self._restore_connection_controls()
        self._append_system("Conexão encerrada.")
        self._refresh()

    def _on_network_disconnect(self) -> None:
        self.root.after(0, self._handle_network_disconnect)

    def _handle_network_disconnect(self) -> None:
        if self.connection is None:
            return

        self.connection = None
        self.status_var.set("Conexão perdida")
        self.chat_entry.configure(state=tk.DISABLED)
        self.chat_button.configure(state=tk.DISABLED)
        self.surrender_button.configure(state=tk.DISABLED)
        self._restore_connection_controls()
        self._append_system("O outro jogador desconectou.")
        self._refresh()

    def _connection_error(self, error: str) -> None:
        messagebox.showerror("Erro de conexão", error)
        self.status_var.set("Desconectado")
        self.server_socket = None
        self.connection = None
        self.local_player = None
        self.connection_mode = None
        self._restore_connection_controls()

    def _restore_connection_controls(self) -> None:
        self._set_connection_controls(True)
        self.connect_button.configure(state=tk.NORMAL)
        self._update_mode()

    def _set_connection_controls(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.port_entry.configure(state=state)

        for widget in self.root.winfo_children():
            self._change_radio_state(widget, state)

        if enabled and self.mode_var.get() == "client":
            self.host_entry.configure(state=tk.NORMAL)
        else:
            self.host_entry.configure(state=tk.DISABLED)

    def _change_radio_state(
        self,
        widget: tk.Widget,
        state: str,
    ) -> None:
        if isinstance(widget, tk.Radiobutton):
            widget.configure(state=state)

        for child in widget.winfo_children():
            self._change_radio_state(child, state)

    @staticmethod
    def _local_ip() -> str:
        temporary = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            temporary.connect(("8.8.8.8", 80))
            return temporary.getsockname()[0]
        except OSError:
            return "127.0.0.1"
        finally:
            temporary.close()

    @staticmethod
    def _player_name(player: Optional[Player]) -> str:
        if player is Player.WHITE:
            return "Brancas"
        if player is Player.BLACK:
            return "Pretas"
        return "-"

    def _close_window(self) -> None:
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass

        if self.connection:
            self.connection.close()

        self.root.destroy()
