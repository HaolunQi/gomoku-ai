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
    Alpha Beta pruning agent for Gomoku using traditional minimax + iterative deepening.

    Board interface used
    --------------------
    board.legal_moves()       - list[(r, c)]
    board.copy()              - Board          (deep copy)
    board.place(move, stone)  - bool
    board.grid                - tuple[tuple]   (immutable snapshot)

    Plugin hooks (from heuristics/evaluate.py)
    -------------------------------------------
    evaluate(board, stone, weights)   - heuristic shared with RL agent
    order_moves(board, moves, stone)  - move ordering to maximise pruning

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

    # Public interface                                                     
  

    def select_move(self, board, stone):
        """
        Return the best legal move found within budget. Always returns something.

        Uses iterative deepening: search depth 1, then 2, then 3, etc until we run out of time or nodes. 
        Each completed depth gives us a best move, so if the budget runs out mid-search, we always have a complete
        best move from the last finished depth.
        """
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        self._nodes = 0
        self._t0 = time.time()

        # first move from ordered list in case budget expires immediately
        best_move = order_moves(board, moves, stone, self.weights)[0]

        for depth in range(1, self.max_depth + 1):
            move, _ = self._search_root(board, stone, depth)
            if move is not None:
                best_move = move
            if not self._budget_ok():
                break

        return best_move

    # Budget helpers                                                       

    def _time_exceeded(self) -> bool:
        """Check if wall clock time limit has been reached."""
        return (time.time() - self._t0) * 1_000.0 >= float(self.time_budget_ms)

    def _node_exceeded(self) -> bool:
        """Check if node expansion limit has been reached."""
        return self._nodes >= int(self.node_budget)

    def _budget_ok(self) -> bool:
        """Return True if both time and node budgets are still available."""
        return not self._time_exceeded() and not self._node_exceeded()

    # Search                                                               

    def _search_root(self, board, stone, depth: int):
        """
        Root level search. Returns (best_move, best_value).

        Separated from _search_value so we can track which move
        led to the best score. the recursive function only returns values.

        stone is treated as the maximizing player (root_stone) throughout
        the entire search tree.
        """
        best_move, best_val = None, -INF
        alpha, beta = -INF, INF

        for move in order_moves(board, board.legal_moves(), stone, self.weights):
            child = board.copy()
            child.place(move, stone)

            # Root is always the maximizing player, so opponent goes next (minimizing)
            val = self._search_value(
                board=child,
                root_stone=stone,
                current_turn=_opponent(stone),
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
            )

            if val > best_val:
                best_val, best_move = val, move

            alpha = max(alpha, best_val)

            if not self._budget_ok():
                break

        return best_move, best_val

    def _search_value(
        self,
        board,
        root_stone,
        current_turn,
        depth: int,
        alpha: float,
        beta: float,
    ) -> float:
        """
        Recursive minimax alpha-beta value function.

        root_stone  : the agent's stone. we always evaluate from this perspective
        current_turn: whose turn it is at this node (may differ from root_stone)

        When current_turn == root_stone  -> maximizing node (we want the highest score)
        When current_turn != root_stone  -> minimizing node (opponent wants lowest score)

        Alpha-beta pruning:
        alpha = best score root_stone is guaranteed so far
        beta  = best score opponent is guaranteed so far
        If alpha >= beta, we prune. the opponent would never let us reach this branch.
        """
        self._nodes += 1

        # Base cases: terminal state, depth limit, or budget exhausted
        if rules.is_terminal(board.grid) or depth == 0 or not self._budget_ok():
            # Always evaluate from root_stone's perspective for consistency
            return evaluate(board, root_stone, self.weights)

        moves = order_moves(board, board.legal_moves(), current_turn, self.weights)

        if current_turn == root_stone:
            # Maximizing player 
            value = -INF
            for move in moves:
                child = board.copy()
                child.place(move, current_turn)
                val = self._search_value(
                    board=child,
                    root_stone=root_stone,
                    current_turn=_opponent(current_turn),
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                )
                value = max(value, val)
                alpha = max(alpha, value)
                if alpha >= beta:
                    # Beta cutoff. opponent won't allow this branch to be reached
                    break  
            return value

        else:
            # Minimizing player (opponent)
            value = INF
            for move in moves:
                child = board.copy()
                child.place(move, current_turn)
                val = self._search_value(
                    board=child,
                    root_stone=root_stone,
                    current_turn=_opponent(current_turn),
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                )
                value = min(value, val)
                beta = min(beta, value)
                if alpha >= beta:
                    # Alpha cutoff.we already have a better option
                    break  
            return value