import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

from game.board import BLACK, EMPTY, WHITE
from game.game import FanoronaGame, InvalidMove
from network.connection import JsonConnection


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Fanorona em Rede")
        self.root.geometry("1120x700")
        self.game = FanoronaGame()
        self.connection = None
        self.server_socket = None
        self.player = None
        self.is_server = False
        self.selected = None
        self.targets = set()
        self.mode = tk.StringVar(value="server")
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="2520")
        self.status = tk.StringVar(value="Desconectado")
        self.info = tk.StringVar(value="Aguardando conexao")
        self._build()
        self._draw_board()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    # Construção da tela
    def _build(self):
        top = tk.LabelFrame(self.root, text="Conexao", padx=8, pady=8)
        top.pack(fill="x", padx=12, pady=8)
        tk.Radiobutton(top, text="Servidor (Brancas)", variable=self.mode, value="server").pack(side="left")
        tk.Radiobutton(top, text="Cliente (Pretas)", variable=self.mode, value="client").pack(side="left")
        tk.Label(top, text="IP:").pack(side="left", padx=(18, 3))
        tk.Entry(top, textvariable=self.host, width=16).pack(side="left")
        tk.Label(top, text="Porta:").pack(side="left", padx=(10, 3))
        tk.Entry(top, textvariable=self.port, width=7).pack(side="left")
        tk.Button(top, text="Conectar / iniciar", command=self._connect).pack(side="left", padx=12)
        tk.Label(top, textvariable=self.status, anchor="w", fg="#14532d").pack(side="left", fill="x", expand=True)

        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=12)
        left = tk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(left, width=760, height=480, bg="#d8aa68", highlightthickness=1)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._board_click)
        controls = tk.Frame(left)
        controls.pack(fill="x", pady=8)
        tk.Label(controls, textvariable=self.info, font=("Arial", 12, "bold")).pack(side="left")
        tk.Button(controls, text="Encerrar sequencia", command=self._end_chain).pack(side="right")
        tk.Button(controls, text="Desistir", command=self._surrender).pack(side="right", padx=8)

        chat = tk.LabelFrame(body, text="Chat dos jogadores", padx=8, pady=8)
        chat.pack(side="right", fill="both", padx=(12, 0))
        self.chat_history = scrolledtext.ScrolledText(chat, width=34, state="disabled", wrap="word")
        self.chat_history.pack(fill="both", expand=True)
        row = tk.Frame(chat)
        row.pack(fill="x", pady=(8, 0))
        self.chat_entry = tk.Entry(row, width=26, state="disabled")
        self.chat_entry.pack(side="left", fill="x", expand=True)
        self.chat_entry.bind("<Return>", lambda _event: self._send_chat())
        self.send_button = tk.Button(row, text="Enviar", state="disabled", command=self._send_chat)
        self.send_button.pack(side="left", padx=(6, 0))

    #Muda texto de status na tela
    def _set_status(self, text):
        self.status.set(text)

    # Escreve na tela do chat
    def _append_chat(self, author, text):
        """Unico ponto autorizado a escrever no historico do chat."""
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", "{}: {}\n".format(author, text))
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    # Cria a conexão
    def _connect(self):
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            self._set_status("Porta invalida")
            return
        if self.mode.get() == "server":
            self.is_server, self.player = True, WHITE
            self._set_status("Aguardando cliente na porta {}...".format(port))
            threading.Thread(target=self._accept, args=(port,), daemon=True).start()
        else:
            self.is_server, self.player = False, BLACK
            self._set_status("Conectando a {}:{}...".format(self.host.get(), port))
            threading.Thread(target=self._join, args=(self.host.get(), port), daemon=True).start()

    # Caso seja servidor cria oservidor e ele fica aquardando a conexão do cliente
    def _accept(self, port):
        try:
            # IPV4 - TCP
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("", port))
            self.server_socket.listen(1)
            sock, address = self.server_socket.accept()
            self.root.after(0, self._activate_connection, sock, "Cliente conectado: {}".format(address[0]))
        except OSError as error:
            self.root.after(0, self._set_status, "Falha no servidor: {}".format(error))

    # Caso seja cliente ele tenta conetar no servidor
    def _join(self, host, port):
        try:
            sock = socket.create_connection((host, port), timeout=8)
            sock.settimeout(None)
            self.root.after(0, self._activate_connection, sock, "Conectado ao servidor")
        except OSError as error:
            self.root.after(0, self._set_status, "Falha na conexao: {}".format(error))

    def _activate_connection(self, sock, status):
        self.connection = JsonConnection(sock, self._network_message, self._network_disconnect)
        self.connection.start()
        self._set_status(status)
        self.chat_entry.configure(state="normal")
        self.send_button.configure(state="normal")
        if self.is_server:
            self.connection.send({"type": "state", "state": self.game.state()})
        self._refresh()

    def _network_message(self, payload):
        self.root.after(0, self._handle_message, payload)

    def _handle_message(self, payload):
        print(payload)
        message_type = payload.get("type")
        if message_type == "chat":
            self._append_chat("Adversario", str(payload.get("text", "")))
        elif message_type == "state":
            self.game.load_state(payload["state"])
            self._set_status("Estado da partida atualizado")
            self._refresh()
        elif message_type == "move_request" and self.is_server:
            try:
                if self.game.turn != BLACK:
                    raise InvalidMove("Nao e o turno do cliente.")
                self.game.move(payload["origin"], payload["destination"], payload.get("capture_type"))
                self._broadcast_state()
                self._set_status("Jogada do cliente validada")
            except (InvalidMove, KeyError) as error:
                self.connection.send({"type": "error", "message": str(error)})
        elif message_type == "end_chain" and self.is_server and self.game.turn == BLACK:
            if self.game.chain_position:
                self.game.end_turn()
                self._broadcast_state()
        elif message_type == "surrender":
            if self.is_server:
                self.game.surrender(BLACK)
                self._broadcast_state()
            else:
                self._set_status("O adversario desistiu")
        elif message_type == "error":
            self._set_status("Jogada recusada: {}".format(payload.get("message", "erro")))

    def _network_disconnect(self):
        self.root.after(0, self._on_disconnected)

    def _on_disconnected(self):
        self.connection = None
        self.chat_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self._set_status("Conexao encerrada")

    def _send_chat(self):
        text = self.chat_entry.get().strip()
        if not text or not self.connection:
            return
        if self.connection.send({"type": "chat", "text": text}):
            self._append_chat("Voce", text)
            self.chat_entry.delete(0, "end")

    def _board_click(self, event):
        if not self.connection or self.game.winner or self.game.turn != self.player:
            return
        position = self._nearest_position(event.x, event.y)
        if position is None:
            return
        if self.game.board.get(position) == self.player:
            if self.game.chain_position and position != self.game.chain_position:
                return
            self.selected = position
            self.targets = {move[1] for move in self.game.legal_moves(origin_filter=self.game.chain_position) if move[0] == position}
            self._draw_board()
        elif self.selected and position in self.targets:
            options = self.game.capture_options(self.selected, position, self.player)
            capture_type = None
            if len(options) == 2:
                answer = messagebox.askyesno("Tipo de captura", "Usar captura por aproximacao?\n(Nao = afastamento)")
                capture_type = "approach" if answer else "withdrawal"
            elif options:
                capture_type = next(iter(options))
            self._request_move(self.selected, position, capture_type)

    def _request_move(self, origin, destination, capture_type):
        if self.is_server:
            try:
                self.game.move(origin, destination, capture_type)
                self._broadcast_state()
            except InvalidMove as error:
                self._set_status(str(error))
        else:
            self.connection.send({"type": "move_request", "origin": list(origin), "destination": list(destination), "capture_type": capture_type})
        self.selected, self.targets = None, set()
        self._refresh()

    def _broadcast_state(self):
        if self.connection:
            self.connection.send({"type": "state", "state": self.game.state()})
        self._refresh()

    def _end_chain(self):
        if self.game.turn != self.player or not self.game.chain_position:
            return
        if self.is_server:
            self.game.end_turn()
            self._broadcast_state()
        elif self.connection:
            self.connection.send({"type": "end_chain"})

    def _surrender(self):
        if not self.connection or not messagebox.askyesno("Desistir", "Confirmar desistencia?"):
            return
        if self.is_server:
            self.game.surrender(WHITE)
            self.connection.send({"type": "surrender"})
            self._broadcast_state()
        else:
            self.connection.send({"type": "surrender"})

    def _refresh(self):
        if self.game.winner:
            self.info.set("Vencedor: {}".format("Brancas" if self.game.winner == WHITE else "Pretas"))
        else:
            turn = "Brancas" if self.game.turn == WHITE else "Pretas"
            self.info.set("Turno: {} | Brancas: {} | Pretas: {}".format(turn, self.game.board.count(WHITE), self.game.board.count(BLACK)))
        self._draw_board()

    def _geometry(self):
        width = max(self.canvas.winfo_width(), 760)
        height = max(self.canvas.winfo_height(), 480)
        margin = 55
        return margin, margin, (width - 2 * margin) / 8, (height - 2 * margin) / 4

    def _point(self, row, col):
        x0, y0, dx, dy = self._geometry()
        return x0 + col * dx, y0 + row * dy

    def _nearest_position(self, x, y):
        best, distance = None, 10 ** 9
        for row in range(5):
            for col in range(9):
                px, py = self._point(row, col)
                current = (px - x) ** 2 + (py - y) ** 2
                if current < distance:
                    best, distance = (row, col), current
        return best if distance <= 28 ** 2 else None

    def _draw_board(self):
        self.canvas.delete("all")
        for row in range(5):
            for col in range(9):
                origin = (row, col)
                x1, y1 = self._point(row, col)
                for target in self.game.board.neighbors(origin):
                    if target > origin:
                        x2, y2 = self._point(*target)
                        self.canvas.create_line(x1, y1, x2, y2, fill="#4a2d16", width=2)
        for row in range(5):
            for col in range(9):
                position = (row, col)
                x, y = self._point(row, col)
                if position in self.targets:
                    self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill="#31c46c", outline="")
                piece = self.game.board.get(position)
                if piece != EMPTY:
                    fill = "#f7f2e8" if piece == WHITE else "#292929"
                    outline = "#e11d48" if position == self.selected else "#111827"
                    width = 4 if position == self.selected else 2
                    self.canvas.create_oval(x - 20, y - 20, x + 20, y + 20, fill=fill, outline=outline, width=width)

    def _close(self):
        if self.connection:
            self.connection.close()
        if self.server_socket:
            self.server_socket.close()
        self.root.destroy()
