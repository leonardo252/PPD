from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set, Tuple

from game.models import Player, Position


ROWS = 5
COLUMNS = 9


class Board:
    """
    Tabuleiro padrão do Fanorona: 5 linhas por 9 colunas.

    A matriz guarda Player.BLACK, Player.WHITE ou None.
    As conexões são determinadas pelas linhas horizontais, verticais
    e diagonais presentes no tabuleiro tradicional.
    """

    def __init__(self) -> None:
        self.cells: List[List[Optional[Player]]] = [
            [None for _ in range(COLUMNS)] for _ in range(ROWS)
        ]
        self.reset()

    def reset(self) -> None:
        for row in range(ROWS):
            for column in range(COLUMNS):
                self.cells[row][column] = None

        # Configuração inicial tradicional: 22 peças para cada jogador.
        for row in (0, 1):
            for column in range(COLUMNS):
                self.cells[row][column] = Player.BLACK

        for row in (3, 4):
            for column in range(COLUMNS):
                self.cells[row][column] = Player.WHITE

        middle = [
            Player.BLACK,
            Player.WHITE,
            Player.BLACK,
            Player.WHITE,
            None,
            Player.BLACK,
            Player.WHITE,
            Player.BLACK,
            Player.WHITE,
        ]

        for column, value in enumerate(middle):
            self.cells[2][column] = value

    def copy(self) -> "Board":
        new_board = Board()
        new_board.cells = [row[:] for row in self.cells]
        return new_board

    def is_inside(self, position: Position) -> bool:
        row, column = position
        return 0 <= row < ROWS and 0 <= column < COLUMNS

    def get(self, position: Position) -> Optional[Player]:
        row, column = position
        return self.cells[row][column]

    def set(self, position: Position, value: Optional[Player]) -> None:
        row, column = position
        self.cells[row][column] = value

    def move_piece(self, origin: Position, destination: Position) -> None:
        piece = self.get(origin)
        self.set(origin, None)
        self.set(destination, piece)

    def remove(self, positions: Iterable[Position]) -> None:
        for position in positions:
            self.set(position, None)

    def count(self, player: Player) -> int:
        return sum(
            1
            for row in self.cells
            for cell in row
            if cell is player
        )

    def positions_for(self, player: Player) -> List[Position]:
        return [
            (row, column)
            for row in range(ROWS)
            for column in range(COLUMNS)
            if self.cells[row][column] is player
        ]

    def neighbors(self, position: Position) -> List[Position]:
        """
        Retorna vizinhos conectados por uma linha do tabuleiro.

        Todas as posições têm conexões horizontal e vertical.
        As diagonais existem nos cruzamentos cuja soma linha+coluna é par.
        """
        row, column = position
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1)
        ]

        if (row + column) % 2 == 0:
            directions.extend([
                (-1, -1), (-1, 1), (1, -1), (1, 1)
            ])

        result: List[Position] = []

        for delta_row, delta_column in directions:
            candidate = (row + delta_row, column + delta_column)
            if self.is_inside(candidate):
                result.append(candidate)

        return result
