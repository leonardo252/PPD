from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from game.board import Board
from game.models import CaptureType, Player, Position


Direction = Tuple[int, int]


class FanoronaRules:
    @staticmethod
    def direction(
        origin: Position,
        destination: Position,
    ) -> Direction:
        return (
            destination[0] - origin[0],
            destination[1] - origin[1],
        )

    @staticmethod
    def add(
        position: Position,
        direction: Direction,
    ) -> Position:
        return (
            position[0] + direction[0],
            position[1] + direction[1],
        )

    @staticmethod
    def subtract(
        position: Position,
        direction: Direction,
    ) -> Position:
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
        result: List[Position] = []
        current = start

        while board.is_inside(current) and board.get(current) is opponent:
            result.append(current)
            current = cls.add(current, direction)

        return result

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

        direction = cls.direction(origin, destination)
        options: Dict[CaptureType, List[Position]] = {}

        approach_start = cls.add(destination, direction)

        if board.is_inside(approach_start):
            approach = cls.capture_line(
                board,
                approach_start,
                direction,
                player.opponent,
            )
            if approach:
                options[CaptureType.APPROACH] = approach

        withdrawal_start = cls.subtract(origin, direction)
        reverse_direction = (-direction[0], -direction[1])

        if board.is_inside(withdrawal_start):
            withdrawal = cls.capture_line(
                board,
                withdrawal_start,
                reverse_direction,
                player.opponent,
            )
            if withdrawal:
                options[CaptureType.WITHDRAWAL] = withdrawal

        return options

    @classmethod
    def has_any_capture(
        cls,
        board: Board,
        player: Player,
    ) -> bool:
        for origin in board.positions_for(player):
            for destination in board.neighbors(origin):
                if board.get(destination) is None:
                    if cls.capture_options(
                        board,
                        origin,
                        destination,
                        player,
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
        destinations: List[Position] = []

        if board.get(origin) is not player:
            return destinations

        for destination in board.neighbors(origin):
            if board.get(destination) is not None:
                continue

            if destination in visited:
                continue

            direction = cls.direction(origin, destination)

            if previous_direction is not None and direction == previous_direction:
                continue

            captures = cls.capture_options(
                board,
                origin,
                destination,
                player,
            )

            if capture_required and not captures:
                continue

            destinations.append(destination)

        return destinations
