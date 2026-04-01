import random

from agents.base import Agent
from gomoku.board import BLACK, WHITE

try:
    from heuristics.features import featurize_after_move
except Exception:
    def featurize_after_move(board, stone, move):
        return {"bias": 1.0}


class RLAgent(Agent):
    """Q-learning agent with linear function approximation.

    Q(s, a) = w · phi(s, a)

    Uses epsilon-greedy for exploration during training.
    During evaluation, set epsilon=0 for purely greedy play.
    """

    name = "rl"

    def __init__(self, weights=None, alpha=0.01, gamma=0.99, epsilon=0.1, seed=0):
        self.weights = dict(weights or {})
        self.alpha = float(alpha)      # learning rate
        self.gamma = float(gamma)      # discount factor
        self.epsilon = float(epsilon)  # exploration rate
        self._rng = random.Random(seed)

    def select_move(self, board, stone):
        moves = board.candidate_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")

        # Epsilon-greedy exploration
        if self._rng.random() < self.epsilon:
            return self._rng.choice(moves)

        # Greedy: pick move with highest Q-value
        best_m = moves[0]
        best_q = None
        for m in moves:
            q = self.q_value(board, stone, m)
            if best_q is None or q > best_q:
                best_q = q
                best_m = m
        return best_m

    def q_value(self, board, stone, move):
        """Compute Q(s, a) = w · phi(s, a)."""
        feats = featurize_after_move(board, stone, move)
        q = 0.0
        for k, v in feats.items():
            q += float(self.weights.get(k, 0.0)) * float(v)
        return float(q)

    def best_q(self, board, stone):
        """Return max_a Q(s, a) over all legal moves, or 0.0 if no moves."""
        moves = board.legal_moves()
        if not moves:
            return 0.0
        return max(self.q_value(board, stone, m) for m in moves)

    def update(self, board, stone, move, reward, next_board, next_stone, done):
        """Semi-gradient Q-learning weight update.

        target = reward                             (if done)
        target = reward + gamma * max_a' Q(s', a')  (otherwise)
        error  = target - Q(s, a)
        w_i   += alpha * error * phi_i(s, a)
        """
        # Current Q-value and features for (s, a)
        feats = featurize_after_move(board, stone, move)
        current_q = 0.0
        for k, v in feats.items():
            current_q += float(self.weights.get(k, 0.0)) * float(v)

        # Compute TD target
        if done:
            target = reward
        else:
            target = reward + self.gamma * self.best_q(next_board, next_stone)

        error = target - current_q

        # Clip error to prevent divergence
        error = max(-10.0, min(10.0, error))

        # Update weights
        for k, v in feats.items():
            fv = float(v)
            if fv == 0.0:
                continue
            old_w = float(self.weights.get(k, 0.0))
            new_w = old_w + self.alpha * error * fv
            # Clip weights to prevent divergence
            self.weights[k] = max(-10.0, min(10.0, new_w))