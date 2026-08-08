from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


Position = Tuple[int, int]


class Player(Enum):
    BLACK = "black"
    WHITE = "white"

    @property
    def opponent(self) -> "Player":
        return Player.WHITE if self is Player.BLACK else Player.BLACK


class CaptureType(Enum):
    APPROACH = "approach"
    WITHDRAWAL = "withdrawal"


@dataclass(frozen=True)
class Move:
    origin: Position
    destination: Position
    capture_type: Optional[CaptureType] = None


@dataclass
class MoveResult:
    success: bool
    message: str
    captured: List[Position]
    turn_continues: bool
    winner: Optional[Player] = None
