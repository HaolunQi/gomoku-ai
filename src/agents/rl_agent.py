import random

from agents.base import Agent
from gomoku.board import BLACK, WHITE

# TODO: fix import path if needed
try:
    from heuristics.features import featurize_after_move
except Exception:
    def featurize_after_move(board, stone, move):
        return {"bias": 1.0}

class RLAgent(Agent):
    # Lightweight feature-based Q-learning skeleton (small board only)
    #
    # Q(s,a) ~ w · phi(s,a)
    # TODO: implement:
    #   - epsilon-greedy
    #   - feature extraction for (state, action)
    #   - (optional) eligibility traces
    #   - training loop in rl/train.py

    name = "rl"

    def __init__(self, weights=None, epsilon=0.1, seed=0):
        self.weights = dict(weights or {})
        self.epsilon = float(epsilon)
        self._rng = random.Random(seed)

    def select_move(self, board, stone):
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        # Epsilon exploration
        if self._rng.random() < self.epsilon:
            return self._rng.choice(moves)

        # Greedy by linear Q estimate (placeholder)
        best_m = moves[0]
        best_q = None
        for m in moves:
            q = self.q_value(board, stone, m)
            if best_q is None or q > best_q:
                best_q = q
                best_m = m
        return best_m

    def q_value(self, board, stone, move):
        # Compute w · phi(board, stone, move)
        feats = featurize_after_move(board, stone, move)
        q = 0.0
        for k, v in feats.items():
            q += float(self.weights.get(k, 0.0)) * float(v)
        return float(q)

    # --- Update placeholders (training only; not used in select_move) ---

    def update(self, transition):
        # TODO: implement Q-learning weight update:
        # transition = (s_board, s_stone, action, reward, s2_board, done)
        return
