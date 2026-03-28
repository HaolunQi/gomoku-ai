import time

from agents.base import Agent
from gomoku.board import BLACK, WHITE
from gomoku import rules

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


class _SearchCutoff(Exception):
    # Internal exception used when time/node budget is exceeded
    pass


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
        moves = board.candidate_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        # Reset budgets
        self._nodes = 0
        self._t0 = time.time()

        # Good fallback in case search is cut off immediately
        ordered_moves = order_moves(board, moves, stone, self.weights)
        best_move = ordered_moves[0]

        # Iterative deepening: keep the best fully completed depth result
        for depth in range(1, self.max_depth + 1):
            try:
                move, _value = self._search_root(board, stone, depth)
                if move is not None:
                    best_move = move
            except _SearchCutoff:
                break

        return best_move

    def _other(self, stone):
        return WHITE if stone == BLACK else BLACK

    def _check_budget(self):
        if self._time_exceeded() or self._node_exceeded():
            raise _SearchCutoff

    def _time_exceeded(self):
        # Enforce time budget
        return (time.time() - self._t0) * 1000.0 >= float(self.time_budget_ms)

    def _node_exceeded(self):
        # Enforce node budget
        return self._nodes >= int(self.node_budget)

    def _search_root(self, board, stone, depth):
        # Root search that returns (best_move, best_value)
        self._check_budget()

        moves = board.candidate_moves()
        if not moves:
            return None, evaluate(board, stone, self.weights)

        moves = order_moves(board, moves, stone, self.weights)

        best_move = None
        best_value = float("-inf")
        alpha = float("-inf")
        beta = float("inf")

        for move in moves:
            self._check_budget()

            child = board.copy()
            ok = child.place(move, stone)
            if not ok:
                continue

            value = self._search_value(
                board=child,
                root_stone=stone,
                current_turn=self._other(stone),
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
            )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

        if best_move is None:
            # Fallback if something strange happens
            return moves[0], evaluate(board, stone, self.weights)

        return best_move, best_value

    def _search_value(self, board, root_stone, current_turn, depth, alpha, beta):
        # Recursive alpha-beta value function
        self._check_budget()
        self._nodes += 1

        # Terminal or cutoff
        if depth == 0 or rules.is_terminal(board.grid):
            return evaluate(board, root_stone, self.weights)

        moves = board.candidate_moves()
        if not moves:
            return evaluate(board, root_stone, self.weights)

        moves = order_moves(board, moves, current_turn, self.weights)

        # Max node: root player's turn
        if current_turn == root_stone:
            value = float("-inf")
            for move in moves:
                self._check_budget()

                child = board.copy()
                ok = child.place(move, current_turn)
                if not ok:
                    continue

                child_value = self._search_value(
                    board=child,
                    root_stone=root_stone,
                    current_turn=self._other(current_turn),
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                )

                if child_value > value:
                    value = child_value
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            return value

        # Min node: opponent's turn
        value = float("inf")
        for move in moves:
            self._check_budget()

            child = board.copy()
            ok = child.place(move, current_turn)
            if not ok:
                continue

            child_value = self._search_value(
                board=child,
                root_stone=root_stone,
                current_turn=self._other(current_turn),
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
            )

            if child_value < value:
                value = child_value
            if value < beta:
                beta = value
            if alpha >= beta:
                break

        return value
