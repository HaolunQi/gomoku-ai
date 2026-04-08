from agents.base import Agent
from gomoku import rules
from gomoku.board import BLACK, WHITE


class GreedyAgent(Agent):
    name = "greedy"

    def select_move(self, board, stone):
        moves = board.candidate_moves()
        if not moves:
            raise RuntimeError("No candidate moves available (game is over).")

        # Immediate win
        for m in moves:
            b2 = board.copy()
            b2.place(m, stone)
            if rules.winner(b2.grid) == stone:
                return m

        # Immediate block
        opp = WHITE if stone == BLACK else BLACK
        for m in moves:
            b2 = board.copy()
            b2.place(m, opp)
            if rules.winner(b2.grid) == opp:
                return m

        # Prefer center (Manhattan distance), deterministic tie-break
        center = (board.size // 2, board.size // 2)

        def key(m):
            return (abs(m[0] - center[0]) + abs(m[1] - center[1]), m[0], m[1])

        return min(moves, key=key)
