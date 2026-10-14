import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext

import Pyro5.errors

from game.board import BLACK, COLS, EMPTY, ROWS, WHITE
from game.game import FanoronaGame
from remote.client import LocalGateway, PyroGateway
from remote.server import PyroServer
from remote.service import FanoronaService


class MainWindow:
    POLL_INTERVAL_MS = 350

    def __init__(self, root):
        self.root = root
        self.root.title("Fanorona - Projeto RMI/RPC com Pyro5")
        self.root.geometry("1180x760")
        self.root.minsize(960, 650)

        self.game = FanoronaGame()
        self.gateway = None
        self.pyro_server = None
        self.token = None
        self.player = None
        self.selected = None
        self.targets = set()
        self.last_version = -1
        self.last_message_id = 0
        self.polling = False
        self.closing = False

        self.mode = tk.StringVar(value="server")
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")
        self.player_name = tk.StringVar(value="Jogador 1")
        self.status = tk.StringVar(value="Desconectado")
        self.operation = tk.StringVar(value="Nenhuma operacao remota")
        self.info = tk.StringVar(value="Configure a conexao para iniciar")

        self._build_interface()
        self._update_mode()
        self._draw_board()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build_interface(self):
        connection = tk.LabelFrame(self.root, text="Conexao Pyro5", padx=10, pady=9)
        connection.pack(fill="x", padx=12, pady=(10, 6))

        self.server_radio = tk.Radiobutton(
            connection, text="Servidor (Brancas)", variable=self.mode,
            value="server", command=self._update_mode,
        )
        self.server_radio.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.client_radio = tk.Radiobutton(
            connection, text="Cliente (Pretas)", variable=self.mode,
            value="client", command=self._update_mode,
        )
        self.client_radio.grid(row=0, column=1, padx=(0, 14), sticky="w")

        tk.Label(connection, text="Nome:").grid(row=0, column=2, sticky="e")
        self.name_entry = tk.Entry(connection, textvariable=self.player_name, width=14)
        self.name_entry.grid(row=0, column=3, padx=(4, 10))
        tk.Label(connection, text="IP:").grid(row=0, column=4, sticky="e")
        self.host_entry = tk.Entry(connection, textvariable=self.host, width=16)
        self.host_entry.grid(row=0, column=5, padx=(4, 10))
        tk.Label(connection, text="Porta:").grid(row=0, column=6, sticky="e")
        self.port_entry = tk.Entry(connection, textvariable=self.port, width=7)
        self.port_entry.grid(row=0, column=7, padx=(4, 10))
        self.connect_button = tk.Button(connection, width=17, command=self._connect)
        self.connect_button.grid(row=0, column=8, padx=(0, 10))
        connection.columnconfigure(9, weight=1)
        tk.Label(connection, textvariable=self.status, anchor="w", fg="#14532d").grid(
            row=0, column=9, sticky="ew"
        )

        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=12, pady=6)
        board_frame = tk.Frame(body)
        board_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            board_frame, width=780, height=520, bg="#d8aa68", highlightthickness=1
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._board_click)
        self.canvas.bind("<Configure>", lambda _event: self._draw_board())

        controls = tk.Frame(board_frame)
        controls.pack(fill="x", pady=(8, 0))
        tk.Label(controls, textvariable=self.info, font=("Arial", 12, "bold")).pack(side="left")
        self.end_button = tk.Button(
            controls, text="Encerrar sequencia", state="disabled", command=self._end_chain
        )
        self.end_button.pack(side="right")
        self.surrender_button = tk.Button(
            controls, text="Desistir", state="disabled", command=self._surrender
        )
        self.surrender_button.pack(side="right", padx=8)

        side = tk.Frame(body, width=320)
        side.pack(side="right", fill="both", padx=(12, 0))
        operation_frame = tk.LabelFrame(side, text="Interface de operacoes", padx=8, pady=8)
        operation_frame.pack(fill="x", pady=(0, 8))
        tk.Label(
            operation_frame, textvariable=self.operation, justify="left",
            anchor="w", wraplength=290,
        ).pack(fill="x")

        chat = tk.LabelFrame(side, text="Chat dos jogadores", padx=8, pady=8)
        chat.pack(fill="both", expand=True)
        self.chat_history = scrolledtext.ScrolledText(
            chat, width=34, state="disabled", wrap="word", font=("Arial", 10)
        )
        self.chat_history.pack(fill="both", expand=True)
        chat_row = tk.Frame(chat)
        chat_row.pack(fill="x", pady=(8, 0))
        self.chat_entry = tk.Entry(chat_row, state="disabled")
        self.chat_entry.pack(side="left", fill="x", expand=True)
        self.chat_entry.bind("<Return>", lambda _event: self._send_chat())
        self.send_button = tk.Button(
            chat_row, text="Enviar", state="disabled", command=self._send_chat
        )
        self.send_button.pack(side="left", padx=(6, 0))

    def _update_mode(self):
        if self.gateway:
            return
        server = self.mode.get() == "server"
        self.host_entry.configure(state="disabled" if server else "normal")
        self.connect_button.configure(text="Hospedar partida" if server else "Conectar")
        self.player_name.set("Jogador 1" if server else "Jogador 2")

    def _validate_connection_fields(self):
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            self._set_status("Porta invalida")
            return None
        if not self.player_name.get().strip():
            self._set_status("Informe o nome do jogador")
            return None
        return port

    def _connect(self):
        if self.gateway:
            return
        port = self._validate_connection_fields()
        if port is None:
            return
        player_name = self.player_name.get().strip()
        self._set_connection_controls("disabled")
        if self.mode.get() == "server":
            self._set_status("Iniciando objeto remoto Pyro...")
            threading.Thread(target=self._host_worker, args=(port, player_name), daemon=True).start()
        else:
            host = self.host.get().strip()
            self._set_status("Conectando ao objeto remoto {}:{}...".format(host, port))
            threading.Thread(target=self._join_worker, args=(host, port, player_name), daemon=True).start()

    def _host_worker(self, port, player_name):
        try:
            service = FanoronaService()
            server = PyroServer(service, "0.0.0.0", port)
            uri = server.start()
            gateway = LocalGateway(service)
            response = gateway.call("join_game", player_name)
            self.root.after(0, self._connected, gateway, response, server, uri)
        except Exception as error:
            self.root.after(0, self._connection_failed, "Falha ao hospedar: {}".format(error))

    def _join_worker(self, host, port, player_name):
        gateway = None
        try:
            gateway = PyroGateway(host, port)
            response = gateway.call("join_game", player_name)
            if not response.get("success"):
                raise RuntimeError(response.get("error", "Entrada recusada"))
            self.root.after(0, self._connected, gateway, response, None, "{}:{}".format(host, port))
        except Exception as error:
            if gateway:
                gateway.close()
            self.root.after(0, self._connection_failed, "Falha na conexao Pyro: {}".format(error))

    def _connected(self, gateway, response, server, address):
        if self.closing:
            gateway.close()
            if server:
                server.close()
            return
        self.gateway = gateway
        self.pyro_server = server
        self.token = response["token"]
        self.player = response["color"]
        self._apply_snapshot(response["snapshot"])
        self._set_status("Conectado como {}".format(self._color_name(self.player)))
        self._set_operation("join_game", "sucesso", address)
        self.chat_entry.configure(state="normal")
        self.send_button.configure(state="normal")
        self.surrender_button.configure(state="normal")
        self.polling = True
        self.root.after(self.POLL_INTERVAL_MS, self._schedule_poll)

    def _connection_failed(self, message):
        self._set_status(message)
        self._set_connection_controls("normal")
        self._update_mode()

    def _schedule_poll(self):
        if not self.polling or self.closing or not self.gateway:
            return
        threading.Thread(target=self._poll_worker, daemon=True).start()

    def _poll_worker(self):
        try:
            started = time.perf_counter()
            snapshot = self.gateway.call("get_snapshot", self.token, self.last_version)
            messages = self.gateway.call("get_messages", self.token, self.last_message_id)
            latency = (time.perf_counter() - started) * 1000
            self.root.after(0, self._handle_poll, snapshot, messages, latency)
        except Exception as error:
            self.root.after(0, self._remote_failure, error)

    def _handle_poll(self, response, messages_response, latency):
        if response.get("changed"):
            self._apply_snapshot(response["snapshot"])
        for message in messages_response.get("messages", []):
            self.last_message_id = max(self.last_message_id, int(message["id"]))
            self._append_chat(message["author"], message["text"])
        self._set_operation("get_snapshot / get_messages", "sucesso", "{:.1f} ms".format(latency))
        if self.polling:
            self.root.after(self.POLL_INTERVAL_MS, self._schedule_poll)

    def _remote_call(self, method, args, callback=None):
        if not self.gateway:
            return

        def worker():
            started = time.perf_counter()
            try:
                response = self.gateway.call(method, *args)
                latency = (time.perf_counter() - started) * 1000
                self.root.after(0, self._handle_remote_response, method, response, latency, callback)
            except Exception as error:
                self.root.after(0, self._remote_failure, error)

        threading.Thread(target=worker, daemon=True).start()

    def _handle_remote_response(self, method, response, latency, callback):
        if not response.get("success"):
            error = response.get("error", "Operacao recusada")
            self._set_status(error)
            self._set_operation(method, "recusada", error)
            return
        snapshot = response.get("snapshot")
        if snapshot:
            self._apply_snapshot(snapshot)
        self._set_operation(method, "sucesso", "{:.1f} ms".format(latency))
        if callback:
            callback(response)

    def _remote_failure(self, error):
        self.polling = False
        self._set_status("Conexao remota encerrada: {}".format(error))
        self._set_operation("chamada remota", "falha", str(error))
        self.chat_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.surrender_button.configure(state="disabled")
        self.end_button.configure(state="disabled")

    def _apply_snapshot(self, snapshot):
        self.last_version = int(snapshot["version"])
        self.game.load_state(snapshot["game"])
        players = snapshot.get("players", {})
        if not snapshot.get("started"):
            self.info.set("Aguardando o segundo jogador")
        elif self.game.winner:
            winner_name = players.get(self.game.winner, self._color_name(self.game.winner))
            self.info.set("Vencedor: {}".format(winner_name))
        else:
            turn_name = players.get(self.game.turn, self._color_name(self.game.turn))
            self.info.set(
                "Turno: {} | Brancas: {} | Pretas: {}".format(
                    turn_name,
                    self.game.board.count(WHITE),
                    self.game.board.count(BLACK),
                )
            )
        can_end = self.game.chain_position is not None and self.game.turn == self.player
        self.end_button.configure(state="normal" if can_end else "disabled")
        self.selected = None
        self.targets.clear()
        self._draw_board()

    def _board_click(self, event):
        if not self.gateway or self.game.winner or self.game.turn != self.player:
            return
        position = self._nearest_position(event.x, event.y)
        if position is None:
            return
        if self.game.board.get(position) == self.player:
            if self.game.chain_position and position != self.game.chain_position:
                return
            self.selected = position
            self.targets = {
                move[1]
                for move in self.game.legal_moves(origin_filter=self.game.chain_position)
                if move[0] == position
            }
            self._draw_board()
            return
        if self.selected and position in self.targets:
            options = self.game.capture_options(self.selected, position, self.player)
            capture_type = None
            if len(options) == 2:
                approach = messagebox.askyesno(
                    "Tipo de captura",
                    "Usar captura por aproximacao?\nEscolha Nao para afastamento.",
                )
                capture_type = "approach" if approach else "withdrawal"
            elif options:
                capture_type = next(iter(options))
            origin = list(self.selected)
            destination = list(position)
            self.selected = None
            self.targets.clear()
            self._draw_board()
            self._remote_call("make_move", (self.token, origin, destination, capture_type))

    def _end_chain(self):
        self._remote_call("end_capture_sequence", (self.token,))

    def _surrender(self):
        if messagebox.askyesno("Desistir", "Deseja realmente desistir da partida?"):
            self._remote_call("surrender", (self.token,))

    def _send_chat(self):
        text = self.chat_entry.get().strip()
        if not text:
            return
        self.chat_entry.delete(0, "end")
        self._remote_call("send_chat", (self.token, text))

    def _append_chat(self, author, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", "{}: {}\n".format(author, text))
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    def _set_status(self, text):
        self.status.set(text)

    def _set_operation(self, name, result, detail):
        self.operation.set(
            "Operacao: {}\nResultado: {}\nDetalhe: {}\nVersao do estado: {}".format(
                name, result, detail, max(self.last_version, 0)
            )
        )

    def _set_connection_controls(self, state):
        self.server_radio.configure(state=state)
        self.client_radio.configure(state=state)
        self.name_entry.configure(state=state)
        self.port_entry.configure(state=state)
        self.connect_button.configure(state=state)
        if self.mode.get() == "client":
            self.host_entry.configure(state=state)

    @staticmethod
    def _color_name(color):
        return "Brancas" if color == WHITE else "Pretas"

    def _geometry(self):
        width = max(self.canvas.winfo_width(), 760)
        height = max(self.canvas.winfo_height(), 480)
        margin = 55
        return margin, margin, (width - 2 * margin) / (COLS - 1), (height - 2 * margin) / (ROWS - 1)

    def _point(self, row, col):
        x0, y0, dx, dy = self._geometry()
        return x0 + col * dx, y0 + row * dy

    def _nearest_position(self, x, y):
        best = None
        distance = float("inf")
        for row in range(ROWS):
            for col in range(COLS):
                px, py = self._point(row, col)
                current = (px - x) ** 2 + (py - y) ** 2
                if current < distance:
                    best, distance = (row, col), current
        return best if distance <= 28 ** 2 else None

    def _draw_board(self):
        self.canvas.delete("all")
        for row in range(ROWS):
            for col in range(COLS):
                origin = (row, col)
                x1, y1 = self._point(row, col)
                for target in self.game.board.neighbors(origin):
                    if target > origin:
                        x2, y2 = self._point(*target)
                        self.canvas.create_line(x1, y1, x2, y2, fill="#4a2d16", width=2)
        for row in range(ROWS):
            for col in range(COLS):
                position = (row, col)
                x, y = self._point(row, col)
                if position in self.targets:
                    self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill="#31c46c", outline="")
                piece = self.game.board.get(position)
                if piece != EMPTY:
                    fill = "#f7f2e8" if piece == WHITE else "#292929"
                    outline = "#e11d48" if position == self.selected else "#111827"
                    width = 4 if position == self.selected else 2
                    self.canvas.create_oval(
                        x - 20, y - 20, x + 20, y + 20,
                        fill=fill, outline=outline, width=width,
                    )

    def _close(self):
        self.closing = True
        self.polling = False
        gateway = self.gateway
        self.gateway = None
        if gateway and self.token:
            try:
                gateway.call("leave_game", self.token)
            except Exception:
                pass
            try:
                gateway.close()
            except Exception:
                pass
        if self.pyro_server:
            try:
                self.pyro_server.close()
            except Exception:
                pass
        self.root.destroy()
