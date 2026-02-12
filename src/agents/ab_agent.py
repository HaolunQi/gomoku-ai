import time

from agents.base import Agent
from gomoku.board import BLACK, WHITE

# TODO: fix import path if needed
try:
    from heuristics.evaluate import evaluate
    from heuristics.evaluate import order_moves
except Exception:
    # Keep importable even if package path isn't ready yet
    def evaluate(board, stone, weights=None):
        # TODO: replace with real evaluator (shared with RL)
        return 0.0

    def order_moves(board, moves, stone, weights=None):
        # TODO: replace with real move ordering (shared)
        return list(moves)

class AlphaBetaAgent(Agent):
    # AlphaBeta skeleton with plugin hooks (evaluate/order_moves)
    name = "alphabeta"

    def __init__(self, max_depth=2, node_budget=5000, time_budget_ms=200, weights=None):
        self.max_depth = max_depth
        self.node_budget = node_budget
        self.time_budget_ms = time_budget_ms
        self.weights = weights

        # Internal counters for budgets
        self._nodes = 0
        self._t0 = 0.0

    def select_move(self, board, stone):
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        # Reset budgets
        self._nodes = 0
        self._t0 = time.time()

        # Basic ordering hook (important for AB later)
        moves = order_moves(board, moves, stone, self.weights)

        # TODO: implement real iterative deepening loop (depth 1..max_depth)
        # TODO: implement alpha-beta recursion:
        #   - terminal test: rules.is_terminal(board.grid)
        #   - depth cutoff
        #   - evaluate(board, stone, weights)
        #   - alpha/beta updates
        # TODO: enforce budgets:
        #   - node_budget: stop when self._nodes >= node_budget
        #   - time_budget_ms: stop when elapsed_ms >= time_budget_ms
        #
        # For now, keep behavior deliverable and legal: pick first ordered move.
        return moves[0]

    # --- Placeholder scaffolding for teammate A to fill in ---

    def _time_exceeded(self):
        # TODO: enforce time budget precisely
        return (time.time() - self._t0) * 1000.0 >= float(self.time_budget_ms)

    def _node_exceeded(self):
        # TODO: enforce node budget precisely
        return self._nodes >= int(self.node_budget)

    def _search_root(self, board, stone, depth):
        # TODO: root search that returns (best_move, best_value)
        # Keep placeholder so imports don't crash
        return None, 0.0

    def _search_value(self, board, stone, depth, alpha, beta):
        # TODO: recursive alpha-beta value function
        return 0.0
