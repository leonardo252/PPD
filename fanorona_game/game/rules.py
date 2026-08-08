from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from game.board import Board
from game.models import CaptureType, Move, Player, Position


Direction = Tuple[int, int]


class FanoronaRules:
    @staticmethod
    def direction(origin: Position, destination: Position) -> Direction:
        return (
            destination[0] - origin[0],
            destination[1] - origin[1],
        )

    @staticmethod
    def add(position: Position, direction: Direction) -> Position:
        return (
            position[0] + direction[0],
            position[1] + direction[1],
        )

    @staticmethod
    def subtract(position: Position, direction: Direction) -> Position:
        return (
            position[0] - direction[0],
            position[1] - direction[1],
        )

    @classmethod
    def capture_line(
        cls,
        board: Board,
        start: Position,
        direction: Direction,
        opponent: Player,
    ) -> List[Position]:
        captured: List[Position] = []
        current = start

        while board.is_inside(current) and board.get(current) is opponent:
            captured.append(current)
            current = cls.add(current, direction)

        return captured

    @classmethod
    def approach_captures(
        cls,
        board: Board,
        origin: Position,
        destination: Position,
        player: Player,
    ) -> List[Position]:
        direction = cls.direction(origin, destination)
        first = cls.add(destination, direction)

        if not board.is_inside(first):
            return []

        return cls.capture_line(
            board,
            first,
            direction,
            player.opponent,
        )

    @classmethod
    def withdrawal_captures(
        cls,
        board: Board,
        origin: Position,
        destination: Position,
        player: Player,
    ) -> List[Position]:
        direction = cls.direction(origin, destination)
        first = cls.subtract(origin, direction)
        reverse = (-direction[0], -direction[1])

        if not board.is_inside(first):
            return []

        return cls.capture_line(
            board,
            first,
            reverse,
            player.opponent,
        )

    @classmethod
    def capture_options(
        cls,
        board: Board,
        origin: Position,
        destination: Position,
        player: Player,
    ) -> Dict[CaptureType, List[Position]]:
        if destination not in board.neighbors(origin):
            return {}

        if board.get(origin) is not player:
            return {}

        if board.get(destination) is not None:
            return {}

        options: Dict[CaptureType, List[Position]] = {}

        approach = cls.approach_captures(
            board, origin, destination, player
        )
        withdrawal = cls.withdrawal_captures(
            board, origin, destination, player
        )

        if approach:
            options[CaptureType.APPROACH] = approach

        if withdrawal:
            options[CaptureType.WITHDRAWAL] = withdrawal

        return options

    @classmethod
    def has_any_capture(cls, board: Board, player: Player) -> bool:
        for origin in board.positions_for(player):
            for destination in board.neighbors(origin):
                if board.get(destination) is None:
                    if cls.capture_options(
                        board, origin, destination, player
                    ):
                        return True
        return False

    @classmethod
    def legal_destinations(
        cls,
        board: Board,
        player: Player,
        origin: Position,
        capture_required: bool,
        visited: Optional[Set[Position]] = None,
        previous_direction: Optional[Direction] = None,
    ) -> List[Position]:
        visited = visited or set()
        result: List[Position] = []

        if board.get(origin) is not player:
            return result

        for destination in board.neighbors(origin):
            if board.get(destination) is not None:
                continue

            if destination in visited:
                continue

            direction = cls.direction(origin, destination)

            # Em sequência de captura, não repetir imediatamente
            # a mesma direção do movimento anterior.
            if previous_direction is not None and direction == previous_direction:
                continue

            options = cls.capture_options(
                board, origin, destination, player
            )

            if capture_required:
                if options:
                    result.append(destination)
            else:
                result.append(destination)

        return result
