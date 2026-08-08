from __future__ import annotations

from typing import Dict, List, Optional, Set

from game.board import Board
from game.models import CaptureType, Move, MoveResult, Player, Position
from game.rules import Direction, FanoronaRules


class FanoronaGame:
    def __init__(self) -> None:
        self.board = Board()
        self.current_player = Player.WHITE
        self.winner: Optional[Player] = None
        self.chain_piece: Optional[Position] = None
        self.visited_positions: Set[Position] = set()
        self.previous_direction: Optional[Direction] = None

    def reset(self) -> None:
        self.board.reset()
        self.current_player = Player.WHITE
        self.winner = None
        self.chain_piece = None
        self.visited_positions.clear()
        self.previous_direction = None

    @property
    def is_capture_chain(self) -> bool:
        return self.chain_piece is not None

    @property
    def capture_is_required(self) -> bool:
        if self.is_capture_chain:
            return True

        return FanoronaRules.has_any_capture(
            self.board,
            self.current_player,
        )

    def legal_destinations(self, origin: Position) -> List[Position]:
        if self.chain_piece is not None and origin != self.chain_piece:
            return []

        return FanoronaRules.legal_destinations(
            board=self.board,
            player=self.current_player,
            origin=origin,
            capture_required=self.capture_is_required,
            visited=self.visited_positions,
            previous_direction=self.previous_direction,
        )

    def capture_options(
        self,
        origin: Position,
        destination: Position,
    ) -> Dict[CaptureType, List[Position]]:
        return FanoronaRules.capture_options(
            self.board,
            origin,
            destination,
            self.current_player,
        )

    def play(self, move: Move) -> MoveResult:
        if self.winner is not None:
            return MoveResult(False, "A partida já terminou.", [], False, self.winner)

        if self.chain_piece is not None and move.origin != self.chain_piece:
            return MoveResult(
                False,
                "A sequência deve continuar com a mesma peça.",
                [],
                True,
            )

        if self.board.get(move.origin) is not self.current_player:
            return MoveResult(
                False,
                "A origem não contém uma peça do jogador atual.",
                [],
                self.is_capture_chain,
            )

        if move.destination not in self.legal_destinations(move.origin):
            return MoveResult(
                False,
                "Movimento inválido.",
                [],
                self.is_capture_chain,
            )

        options = self.capture_options(move.origin, move.destination)
        captured: List[Position] = []

        if options:
            if move.capture_type is None:
                return MoveResult(
                    False,
                    "Escolha aproximação ou afastamento.",
                    [],
                    self.is_capture_chain,
                )

            captured = options.get(move.capture_type, [])

            if not captured:
                return MoveResult(
                    False,
                    "Tipo de captura inválido.",
                    [],
                    self.is_capture_chain,
                )

        elif self.capture_is_required:
            return MoveResult(
                False,
                "Existe uma captura obrigatória.",
                [],
                self.is_capture_chain,
            )

        direction = FanoronaRules.direction(
            move.origin,
            move.destination,
        )

        self.board.move_piece(move.origin, move.destination)
        self.board.remove(captured)

        if self.board.count(self.current_player.opponent) == 0:
            self.winner = self.current_player
            self._clear_chain()

            return MoveResult(
                True,
                "Vitória por captura.",
                captured,
                False,
                self.winner,
            )

        if captured:
            self.visited_positions.add(move.origin)
            self.visited_positions.add(move.destination)
            self.chain_piece = move.destination
            self.previous_direction = direction

            if self.legal_destinations(move.destination):
                return MoveResult(
                    True,
                    "Continue a sequência de capturas.",
                    captured,
                    True,
                )

        self._finish_turn()

        return MoveResult(True, "Movimento realizado.", captured, False)

    def finish_capture_chain(self) -> MoveResult:
        if not self.is_capture_chain:
            return MoveResult(
                False,
                "Não existe sequência ativa.",
                [],
                False,
            )

        self._finish_turn()
        return MoveResult(True, "Sequência encerrada.", [], False)

    def surrender(self, player: Player) -> MoveResult:
        if self.winner is not None:
            return MoveResult(False, "A partida já terminou.", [], False, self.winner)

        self.winner = player.opponent
        self._clear_chain()

        return MoveResult(
            True,
            "Desistência.",
            [],
            False,
            self.winner,
        )

    def serialize(self) -> dict:
        return {
            "board": self.board.serialize(),
            "current_player": self.current_player.value,
            "winner": self.winner.value if self.winner else None,
            "chain_piece": list(self.chain_piece) if self.chain_piece else None,
            "visited_positions": [
                list(position) for position in self.visited_positions
            ],
            "previous_direction": (
                list(self.previous_direction)
                if self.previous_direction
                else None
            ),
        }

    def load_serialized(self, data: dict) -> None:
        self.board.load_serialized(data["board"])
        self.current_player = Player(data["current_player"])
        self.winner = Player(data["winner"]) if data.get("winner") else None

        chain_piece = data.get("chain_piece")
        self.chain_piece = tuple(chain_piece) if chain_piece else None

        self.visited_positions = {
            tuple(position)
            for position in data.get("visited_positions", [])
        }

        previous_direction = data.get("previous_direction")
        self.previous_direction = (
            tuple(previous_direction)
            if previous_direction
            else None
        )

    def _finish_turn(self) -> None:
        self.current_player = self.current_player.opponent
        self._clear_chain()

    def _clear_chain(self) -> None:
        self.chain_piece = None
        self.visited_positions.clear()
        self.previous_direction = None
