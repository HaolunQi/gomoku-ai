from agents.base import Agent
from gomoku import rules
from gomoku.board import BLACK, WHITE



class GreedyAgent(Agent):
    # Baseline agent: win if possible, else block, else prefer center

    name = "greedy"

    def select_move(self, board, stone):
        # Choose a move using a simple one-ply policy
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
        opp = WHITE if stone == BLACK else BLACK
        for m in moves:
            b2 = board.copy()
            b2.place(m, opp)
            if rules.winner(b2.grid) == opp:
                return m

        # 3) Prefer center (Manhattan distance), deterministic tie-break
        center = (board.size // 2, board.size // 2)

        def key(m):
            return (abs(m[0] - center[0]) + abs(m[1] - center[1]), m[0], m[1])

        return min(moves, key=key)
