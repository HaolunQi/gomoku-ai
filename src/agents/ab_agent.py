import time
from agents.base import Agent
from gomoku.board import BLACK, WHITE
from gomoku import rules
from heuristics.evaluate import evaluate, order_moves


class _SearchCutoff(Exception):
    # raised when time/node budget exceeded
    pass


class AlphaBetaAgent(Agent):
    name = "alphabeta"

    def __init__(self, max_depth=2, node_budget=5000, time_budget_ms=200, weights=None):
        # search limits and eval weights
        self.max_depth = max_depth
        self.node_budget = node_budget
        self.time_budget_ms = time_budget_ms
        self.weights = weights

        self._nodes = 0
        self._t0 = 0.0

        self._tt = {}  # transposition table

    def select_move(self, board, stone):
        # iterative deepening with move ordering
        moves = board.candidate_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        self._reset_search_state()

        ordered_moves = order_moves(board, moves, stone, self.weights)
        best_move = ordered_moves[0]

        for depth in range(1, self.max_depth + 1):
            try:
                move, _value = self._search_root(board, stone, depth)
                if move is not None:
                    best_move = move
            except _SearchCutoff:
                break

        return best_move

    def _reset_search_state(self):
        # reset counters and tt
        self._nodes = 0
        self._t0 = time.perf_counter()
        self._tt = {}

    def _other(self, stone):
        return WHITE if stone == BLACK else BLACK

    def _elapsed_ms(self):
        return (time.perf_counter() - self._t0) * 1000.0

    def _time_exceeded(self):
        return self._elapsed_ms() >= float(self.time_budget_ms)

    def _node_exceeded(self):
        return self._nodes >= int(self.node_budget)

    def _check_budget(self):
        # stop search if budget exceeded
        if self._time_exceeded() or self._node_exceeded():
            raise _SearchCutoff

    def _count_node_and_check_budget(self):
        self._nodes += 1
        self._check_budget()

    def _board_key(self, board, current_turn, depth):
        # key for transposition table
        grid_key = tuple(tuple(row) for row in board.grid)
        return (grid_key, current_turn, depth)

    def _lookup_tt(self, board, current_turn, depth):
        # retrieve cached value if depth sufficient
        key = self._board_key(board, current_turn, depth)
        entry = self._tt.get(key)
        if entry is None:
            return None

        stored_depth, stored_value = entry
        if stored_depth >= depth:
            return stored_value
        return None

    def _store_tt(self, board, current_turn, depth, value):
        # store value if deeper
        key = self._board_key(board, current_turn, depth)
        old = self._tt.get(key)
        if old is None or old[0] < depth:
            self._tt[key] = (depth, value)

    def _search_root(self, board, stone, depth):
        # root search (max node)
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
            if not child.place(move, stone):
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

            alpha = max(alpha, value)

        if best_move is None:
            return moves[0], evaluate(board, stone, self.weights)

        return best_move, best_value

    def _search_value(self, board, root_stone, current_turn, depth, alpha, beta):
        # alpha-beta recursion:
        # 1. check budget and count node
        # 2. if terminal or depth==0 -> evaluate and return
        # 3. lookup TT, return if hit
        # 4. generate and order moves
        # 5. recurse:
        #    - max node: maximize value, update alpha
        #    - min node: minimize value, update beta
        # 6. prune when alpha >= beta
        # 7. store in TT and return value
        self._count_node_and_check_budget()

        winner = rules.winner(board.grid)
        if depth == 0 or winner is not None or rules.is_terminal(board.grid):
            value = evaluate(board, root_stone, self.weights)
            self._store_tt(board, current_turn, depth, value)
            return value

        cached = self._lookup_tt(board, current_turn, depth)
        if cached is not None:
            return cached

        moves = board.candidate_moves()
        if not moves:
            value = evaluate(board, root_stone, self.weights)
            self._store_tt(board, current_turn, depth, value)
            return value

        moves = order_moves(board, moves, current_turn, self.weights)

        if current_turn == root_stone:
            # max node
            value = float("-inf")
            for move in moves:
                self._check_budget()

                child = board.copy()
                if not child.place(move, current_turn):
                    continue

                child_value = self._search_value(
                    board=child,
                    root_stone=root_stone,
                    current_turn=self._other(current_turn),
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                )

                value = max(value, child_value)
                alpha = max(alpha, value)

                if alpha >= beta:
                    break
        else:
            # min node
            value = float("inf")
            for move in moves:
                self._check_budget()

                child = board.copy()
                if not child.place(move, current_turn):
                    continue

                child_value = self._search_value(
                    board=child,
                    root_stone=root_stone,
                    current_turn=self._other(current_turn),
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                )

                value = min(value, child_value)
                beta = min(beta, value)

                if alpha >= beta:
                    break

        self._store_tt(board, current_turn, depth, value)
        return value