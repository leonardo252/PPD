ROWS = 5
COLS = 9
EMPTY = "."
WHITE = "W"
BLACK = "B"


class Board:
    def __init__(self, cells=None):
        self.cells = cells if cells is not None else self._initial_cells()

    @staticmethod
    def _initial_cells():
        return [
            [BLACK] * COLS,
            [BLACK] * COLS,
            [BLACK, WHITE, BLACK, WHITE, EMPTY, BLACK, WHITE, BLACK, WHITE],
            [WHITE] * COLS,
            [WHITE] * COLS,
        ]

    def inside(self, position):
        row, col = position
        return 0 <= row < ROWS and 0 <= col < COLS

    def get(self, position):
        row, col = position
        return self.cells[row][col]

    def set(self, position, value):
        row, col = position
        self.cells[row][col] = value

    def connected(self, origin, destination):
        dr = abs(destination[0] - origin[0])
        dc = abs(destination[1] - origin[1])
        if max(dr, dc) != 1 or dr + dc == 0:
            return False
        if dr == 1 and dc == 1:
            return (origin[0] + origin[1]) % 2 == 0
        return True

    def neighbors(self, position):
        row, col = position
        result = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                target = (row + dr, col + dc)
                if self.inside(target) and self.connected(position, target):
                    result.append(target)
        return result

    def count(self, player):
        return sum(row.count(player) for row in self.cells)

    def to_list(self):
        return [row[:] for row in self.cells]
