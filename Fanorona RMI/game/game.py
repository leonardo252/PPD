from game.board import BLACK, COLS, EMPTY, ROWS, WHITE, Board


class InvalidMove(ValueError):
    pass


class FanoronaGame:
    def __init__(self):
        self.board = Board()
        self.turn = WHITE
        self.winner = None
        self.chain_position = None
        self.visited = set()

    @staticmethod
    def opponent(player):
        return BLACK if player == WHITE else WHITE

    def _capture_line(self, origin, destination, mode, player):
        dr = destination[0] - origin[0]
        dc = destination[1] - origin[1]
        if mode == "approach":
            position = (destination[0] + dr, destination[1] + dc)
            step = (dr, dc)
        else:
            position = (origin[0] - dr, origin[1] - dc)
            step = (-dr, -dc)

        captured = []
        enemy = self.opponent(player)
        while self.board.inside(position) and self.board.get(position) == enemy:
            captured.append(position)
            position = (position[0] + step[0], position[1] + step[1])
        return captured

    def capture_options(self, origin, destination, player=None):
        player = player or self.turn
        options = {}
        for mode in ("approach", "withdrawal"):
            pieces = self._capture_line(origin, destination, mode, player)
            if pieces:
                options[mode] = pieces
        return options

    def legal_moves(self, player=None, origin_filter=None):
        player = player or self.turn
        captures = []
        simple = []
        for row in range(ROWS):
            for col in range(COLS):
                origin = (row, col)
                if self.board.get(origin) != player:
                    continue
                if origin_filter is not None and origin != origin_filter:
                    continue
                for destination in self.board.neighbors(origin):
                    if self.board.get(destination) != EMPTY:
                        continue
                    if destination in self.visited:
                        continue
                    options = self.capture_options(origin, destination, player)
                    if options:
                        captures.append((origin, destination, tuple(options)))
                    else:
                        simple.append((origin, destination, ()))
        return captures if captures else simple

    def move(self, origin, destination, capture_type=None):
        origin = tuple(origin)
        destination = tuple(destination)
        if self.winner:
            raise InvalidMove("A partida ja terminou.")
        if self.chain_position is not None and origin != self.chain_position:
            raise InvalidMove("Continue com a mesma peca.")

        legal = self.legal_moves(origin_filter=self.chain_position)
        match = next((move for move in legal if move[:2] == (origin, destination)), None)
        if match is None:
            raise InvalidMove("Movimento invalido ou existe uma captura obrigatoria.")

        options = self.capture_options(origin, destination)
        if len(options) > 1 and capture_type not in options:
            raise InvalidMove("Escolha aproximacao ou afastamento.")
        if options and capture_type is None:
            capture_type = next(iter(options))
        if capture_type is not None and capture_type not in options:
            raise InvalidMove("Tipo de captura invalido.")

        player = self.turn
        self.board.set(origin, EMPTY)
        self.board.set(destination, player)
        captured = options.get(capture_type, [])
        for position in captured:
            self.board.set(position, EMPTY)

        if captured:
            self.visited.update((origin, destination))
            self.chain_position = destination
            following = self.legal_moves(origin_filter=destination)
            if any(move[2] for move in following):
                self._check_winner()
                return captured

        self.end_turn()
        return captured

    def end_turn(self):
        self.chain_position = None
        self.visited.clear()
        self._check_winner()
        if not self.winner:
            self.turn = self.opponent(self.turn)

    def surrender(self, player):
        if not self.winner:
            self.winner = self.opponent(player)

    def _check_winner(self):
        if self.board.count(WHITE) == 0:
            self.winner = BLACK
        elif self.board.count(BLACK) == 0:
            self.winner = WHITE

    def state(self):
        return {
            "board": self.board.to_list(),
            "turn": self.turn,
            "winner": self.winner,
            "chain_position": list(self.chain_position) if self.chain_position else None,
            "visited": [list(position) for position in sorted(self.visited)],
            "white_count": self.board.count(WHITE),
            "black_count": self.board.count(BLACK),
        }

    def load_state(self, state):
        self.board = Board([row[:] for row in state["board"]])
        self.turn = state["turn"]
        self.winner = state.get("winner")
        chain = state.get("chain_position")
        self.chain_position = tuple(chain) if chain else None
        self.visited = {tuple(position) for position in state.get("visited", [])}
