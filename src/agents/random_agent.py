from __future__ import annotations

import random

from agents.base import Agent
from gomoku.board import Board, Stone, Move


class RandomAgent(Agent):
    """Baseline agent: chooses uniformly at random from legal moves."""

    name = "random"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def select_move(self, board: Board, stone: Stone) -> Move:
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")
        return self._rng.choice(moves)
