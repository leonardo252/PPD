from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple

from game.board import COLUMNS, ROWS
from game.game import FanoronaGame
from game.models import CaptureType, Move, Player, Position


class FanoronaWindow:
    CANVAS_WIDTH = 900
    CANVAS_HEIGHT = 500
    MARGIN_X = 70
    MARGIN_Y = 70
    PIECE_RADIUS = 18

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.game = FanoronaGame()
        self.selected: Optional[Position] = None
        self.valid_destinations: List[Position] = []

        self.status_text = tk.StringVar()
        self.black_count_text = tk.StringVar()
        self.white_count_text = tk.StringVar()

        self.root.title("Fanorona")
        self.root.geometry("1040x720")
        self.root.minsize(900, 650)

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, padx=14, pady=12)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="FANORONA",
            font=("Arial", 24, "bold"),
        )
        title.pack(side=tk.LEFT)

        tk.Button(
            header,
            text="Nova partida",
            command=self._new_game,
            padx=14,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(
            header,
            text="Desistir",
            command=self._surrender,
            padx=14,
        ).pack(side=tk.RIGHT)

        content = tk.Frame(self.root, padx=14, pady=4)
        content.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            content,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            background="#d9b77e",
            highlightthickness=1,
            highlightbackground="#5c4328",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", lambda _: self._refresh())

        footer = tk.Frame(self.root, padx=14, pady=12)
        footer.pack(fill=tk.X)

        tk.Label(
            footer,
            textvariable=self.status_text,
            font=("Arial", 13, "bold"),
            anchor="w",
        ).pack(fill=tk.X)

        counters = tk.Frame(footer)
        counters.pack(fill=tk.X, pady=(8, 0))

        tk.Label(
            counters,
            textvariable=self.white_count_text,
            font=("Arial", 11),
        ).pack(side=tk.LEFT)

        tk.Label(
            counters,
            textvariable=self.black_count_text,
            font=("Arial", 11),
        ).pack(side=tk.RIGHT)

        self.finish_chain_button = tk.Button(
            footer,
            text="Encerrar sequência de captura",
            command=self._finish_capture_chain,
            state=tk.DISABLED,
        )
        self.finish_chain_button.pack(pady=(10, 0))

    def _board_geometry(self) -> Tuple[float, float, float, float]:
        width = max(self.canvas.winfo_width(), 300)
        height = max(self.canvas.winfo_height(), 300)

        left = self.MARGIN_X
        top = self.MARGIN_Y
        right = width - self.MARGIN_X
        bottom = height - self.MARGIN_Y

        return left, top, right, bottom

    def _position_to_point(self, position: Position) -> Tuple[float, float]:
        row, column = position
        left, top, right, bottom = self._board_geometry()

        spacing_x = (right - left) / (COLUMNS - 1)
        spacing_y = (bottom - top) / (ROWS - 1)

        return (
            left + column * spacing_x,
            top + row * spacing_y,
        )

    def _point_to_position(self, x: float, y: float) -> Optional[Position]:
        closest: Optional[Position] = None
        closest_distance = float("inf")

        for row in range(ROWS):
            for column in range(COLUMNS):
                point_x, point_y = self._position_to_point(
                    (row, column)
                )
                distance = math.hypot(x - point_x, y - point_y)

                if distance < closest_distance:
                    closest_distance = distance
                    closest = (row, column)

        if closest_distance <= 30:
            return closest

        return None

    def _draw_board(self) -> None:
        self.canvas.delete("all")

        # Linhas entre todos os vizinhos. O conjunto evita duplicação.
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
                        x1,
                        y1,
                        x2,
                        y2,
                        fill="#5c4328",
                        width=2,
                    )

        for row in range(ROWS):
            for column in range(COLUMNS):
                position = (row, column)
                x, y = self._position_to_point(position)

                self.canvas.create_oval(
                    x - 4,
                    y - 4,
                    x + 4,
                    y + 4,
                    fill="#5c4328",
                    outline="",
                )

        for destination in self.valid_destinations:
            x, y = self._position_to_point(destination)
            self.canvas.create_oval(
                x - 13,
                y - 13,
                x + 13,
                y + 13,
                fill="#6fbf73",
                outline="#27632b",
                width=2,
            )

        if self.selected is not None:
            x, y = self._position_to_point(self.selected)
            self.canvas.create_oval(
                x - self.PIECE_RADIUS - 6,
                y - self.PIECE_RADIUS - 6,
                x + self.PIECE_RADIUS + 6,
                y + self.PIECE_RADIUS + 6,
                outline="#e8b923",
                width=4,
            )

        for row in range(ROWS):
            for column in range(COLUMNS):
                position = (row, column)
                player = self.game.board.get(position)

                if player is None:
                    continue

                x, y = self._position_to_point(position)

                fill = "#f5f2e8" if player is Player.WHITE else "#242424"
                outline = "#555555" if player is Player.WHITE else "#000000"

                self.canvas.create_oval(
                    x - self.PIECE_RADIUS,
                    y - self.PIECE_RADIUS,
                    x + self.PIECE_RADIUS,
                    y + self.PIECE_RADIUS,
                    fill=fill,
                    outline=outline,
                    width=2,
                )

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.game.winner is not None:
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
            self._attempt_move(self.selected, position)
            return

        self._select_piece(position)

    def _select_piece(self, position: Position) -> None:
        if self.game.is_capture_chain:
            if position != self.game.chain_piece:
                return

        if self.game.board.get(position) is not self.game.current_player:
            return

        destinations = self.game.legal_destinations(position)

        if not destinations:
            return

        self.selected = position
        self.valid_destinations = destinations
        self._refresh()

    def _attempt_move(
        self,
        origin: Position,
        destination: Position,
    ) -> None:
        options = self.game.capture_options(origin, destination)
        capture_type: Optional[CaptureType] = None

        if len(options) == 1:
            capture_type = next(iter(options.keys()))

        elif len(options) == 2:
            capture_type = self._ask_capture_type()

            if capture_type is None:
                return

        result = self.game.play(
            Move(
                origin=origin,
                destination=destination,
                capture_type=capture_type,
            )
        )

        if not result.success:
            messagebox.showwarning(
                "Movimento inválido",
                result.message,
            )
            return

        if result.turn_continues:
            self.selected = destination
            self.valid_destinations = self.game.legal_destinations(
                destination
            )
        else:
            self.selected = None
            self.valid_destinations = []

        self._refresh()

        if result.winner is not None:
            winner_name = self._player_name(result.winner)
            messagebox.showinfo(
                "Fim da partida",
                "{} venceu!".format(winner_name),
            )

    def _ask_capture_type(self) -> Optional[CaptureType]:
        dialog = tk.Toplevel(self.root)
        dialog.title("Escolha a captura")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        result = {"value": None}

        tk.Label(
            dialog,
            text="Este movimento permite dois tipos de captura.",
            padx=22,
            pady=(18, 8),
            font=("Arial", 11),
        ).pack()

        tk.Label(
            dialog,
            text="Escolha como deseja capturar:",
            padx=22,
            pady=(0, 12),
        ).pack()

        buttons = tk.Frame(dialog, padx=16, pady=14)
        buttons.pack(fill=tk.X)

        def choose(value: CaptureType) -> None:
            result["value"] = value
            dialog.destroy()

        tk.Button(
            buttons,
            text="Aproximação",
            width=15,
            command=lambda: choose(CaptureType.APPROACH),
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons,
            text="Afastamento",
            width=15,
            command=lambda: choose(CaptureType.WITHDRAWAL),
        ).pack(side=tk.LEFT, padx=5)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        self.root.wait_window(dialog)

        return result["value"]

    def _finish_capture_chain(self) -> None:
        result = self.game.finish_capture_chain()

        if result.success:
            self.selected = None
            self.valid_destinations = []
            self._refresh()

    def _surrender(self) -> None:
        if self.game.winner is not None:
            return

        confirmed = messagebox.askyesno(
            "Desistir",
            "Deseja realmente desistir da partida?",
        )

        if not confirmed:
            return

        result = self.game.surrender()
        self.selected = None
        self.valid_destinations = []
        self._refresh()

        if result.winner is not None:
            messagebox.showinfo(
                "Fim da partida",
                "{} venceu por desistência.".format(
                    self._player_name(result.winner)
                ),
            )

    def _new_game(self) -> None:
        confirmed = messagebox.askyesno(
            "Nova partida",
            "Deseja iniciar uma nova partida?",
        )

        if not confirmed:
            return

        self.game.reset()
        self.selected = None
        self.valid_destinations = []
        self._refresh()

    def _refresh(self) -> None:
        self._draw_board()

        white_count = self.game.board.count(Player.WHITE)
        black_count = self.game.board.count(Player.BLACK)

        self.white_count_text.set(
            "Peças brancas: {}".format(white_count)
        )
        self.black_count_text.set(
            "Peças pretas: {}".format(black_count)
        )

        if self.game.winner is not None:
            self.status_text.set(
                "Vencedor: {}".format(
                    self._player_name(self.game.winner)
                )
            )
            self.finish_chain_button.configure(
                state=tk.DISABLED
            )
            return

        current = self._player_name(self.game.current_player)

        if self.game.is_capture_chain:
            self.status_text.set(
                "Turno de {} — continue capturando ou encerre a sequência.".format(
                    current
                )
            )
            self.finish_chain_button.configure(
                state=tk.NORMAL
            )

        elif self.game.capture_is_required:
            self.status_text.set(
                "Turno de {} — existe uma captura obrigatória.".format(
                    current
                )
            )
            self.finish_chain_button.configure(
                state=tk.DISABLED
            )

        else:
            self.status_text.set(
                "Turno de {} — selecione uma peça.".format(current)
            )
            self.finish_chain_button.configure(
                state=tk.DISABLED
            )

    @staticmethod
    def _player_name(player: Player) -> str:
        return "Brancas" if player is Player.WHITE else "Pretas"
