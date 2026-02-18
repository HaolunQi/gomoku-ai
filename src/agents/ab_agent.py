import time
from agents.base import Agent
from gomoku.board import BLACK, WHITE
from gomoku import rules

try:
    from heuristics.evaluate import evaluate
    from heuristics.evaluate import order_moves
except Exception:
    def evaluate(board, stone, weights=None):
        return 0.0
    def order_moves(board, moves, stone, weights=None):
        return list(moves)

INF = float("inf")


def _opponent(stone):
    return WHITE if stone == BLACK else BLACK


class AlphaBetaAgent(Agent):
    """
    Alpha-Beta pruning agent for Gomoku.

    Board interface used
    --------------------
    board.legal_moves()       - list[(r, c)]
    board.copy()              - Board          (deep copy)
    board.place(move, stone)  - bool
    board.grid                - tuple[tuple]   (immutable snapshot)

    Plugin hooks
    ------------
    evaluate(board, stone, weights)   – heuristic shared with RL agent
    order_moves(board, moves, stone)  – move ordering to maximise pruning

    Budget controls
    ---------------
    max_depth      : hard depth limit for iterative deepening
    node_budget    : max nodes expanded per select_move call
    time_budget_ms : max wall-clock ms per select_move call
    """

    name = "alphabeta"

    def __init__(
        self,
        max_depth: int = 2,
        node_budget: int = 5_000,
        time_budget_ms: int = 200,
        weights=None,
    ):
        self.max_depth = max_depth
        self.node_budget = node_budget
        self.time_budget_ms = time_budget_ms
        self.weights = weights

        self._nodes: int = 0
        self._t0: float = 0.0

   	#Public Interface

    def select_move(self, board, stone):
        """Return a legal move. Always returns something (P0 guarantee)."""
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        self._nodes = 0
        self._t0 = time.time()

        moves = order_moves(board, moves, stone, self.weights)

        best_move = moves[0]
        for depth in range(1, self.max_depth + 1):
            move, _ = self._search_root(board, stone, depth)
            if move is not None:
                best_move = move
            if not self._budget_ok():
                break
        return best_move

	#Budget Helpers

    def _time_exceeded(self) -> bool:
        return (time.time() - self._t0) * 1_000.0 >= float(self.time_budget_ms)

    def _node_exceeded(self) -> bool:
        return self._nodes >= int(self.node_budget)

    def _budget_ok(self) -> bool:
        return not self._time_exceeded() and not self._node_exceeded()


	#Search

    def _search_root(self, board, stone, depth: int):
        """Root level search. Returns (best_move, best_value)."""
        best_move, best_val = None, -INF
        moves = order_moves(board, board.legal_moves(), stone, self.weights)
        for move in moves:
            child = board.copy()
            child.place(move, stone)
            val = -self._search_value(child, _opponent(stone), depth - 1, -INF, INF)
            if val > best_val:
                best_val, best_move = val, move
            if not self._budget_ok():
                break
        return best_move, best_val

    def _search_value(self, board, stone, depth: int, alpha: float, beta: float) -> float:
        """Recursive negamax alpha-beta value function."""
        self._nodes += 1

        if rules.is_terminal(board.grid) or depth == 0 or not self._budget_ok():
            return evaluate(board, stone, self.weights)

        for move in order_moves(board, board.legal_moves(), stone, self.weights):
            child = board.copy()
            child.place(move, stone)
            val = -self._search_value(child, _opponent(stone), depth - 1, -beta, -alpha)
            alpha = max(alpha, val)
            if alpha >= beta:
                break  # prune
        return alpha