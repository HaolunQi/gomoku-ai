from __future__ import annotations

from agents.base import Agent
from gomoku.board import Board, BOARD_SIZE, Stone, BLACK, WHITE, Move
from gomoku import rules
from gomoku.game import other

class GreedyAgent(Agent):
    """
    Baseline agent: one-ply tactical policy.

    Priority:
      1) Win immediately if possible.
      2) Block opponent's immediate win if needed.
      3) Otherwise, prefer center, then any move (deterministic).
    """

    name = "greedy"

    def select_move(self, board: Board, stone: Stone) -> Move:
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        # 1) Immediate win
        for m in moves:
            b2 = board.copy()
            b2.place(m, stone)
            if rules.winner(b2.grid) == stone:
                return m

        # 2) Immediate block
        opp = other(stone)
        for m in moves:
            b2 = board.copy()
            b2.place(m, opp)
            if rules.winner(b2.grid) == opp:
                return m

        # 3) Prefer center (closest by Manhattan distance), deterministic tie-break
        center = (BOARD_SIZE // 2, BOARD_SIZE // 2)

        def key(m: Move) -> tuple[int, int, int]:
            return (abs(m[0] - center[0]) + abs(m[1] - center[1]), m[0], m[1])

        return min(moves, key=key)
