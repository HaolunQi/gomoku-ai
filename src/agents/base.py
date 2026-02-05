from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Tuple
from gomoku.board import Board, Stone

Move = Tuple[int, int]

class Agent(ABC):
    name: str = "agent"

    @abstractmethod
    def select_move(self, board: Board, stone: Stone) -> Move:
        raise NotImplementedError
