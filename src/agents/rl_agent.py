import random

from agents.base import Agent
from gomoku import rules
from heuristics.features import extract_features, featurize_after_move



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

        # 1. Immediate win
        for move in moves:
            b = board.copy()
            if b.place(move, stone) and rules.winner(b.grid) == stone:
                return move

        before_feats = extract_features(board, stone)

        opp_three_pressure = (
            before_feats.get("opp_live_three", 0.0)
            + before_feats.get("opp_jump_three", 0.0)
        )

        my_attack_ready = (
            before_feats.get("my_live_three", 0.0) > 0.0
            or before_feats.get("my_jump_three", 0.0) > 0.0
            or before_feats.get("my_live_four", 0.0) > 0.0
            or before_feats.get("my_blocked_four", 0.0) > 0.0
            or before_feats.get("my_jump_four", 0.0) > 0.0
        )

        must_defend_three = (opp_three_pressure > 0.0 and not my_attack_ready)

        move_pool = moves

        if must_defend_three:
            defend_moves = []

            for move in moves:
                b = board.copy()
                if not b.place(move, stone):
                    continue

                after_feats = extract_features(b, stone)

                after_opp_three_pressure = (
                    after_feats.get("opp_live_three", 0.0)
                    + after_feats.get("opp_jump_three", 0.0)
                )

                if after_opp_three_pressure < opp_three_pressure:
                    defend_moves.append(move)

            if defend_moves:
                move_pool = defend_moves

        # Epsilon-greedy exploration
        if self._rng.random() < self.epsilon:
            return self._rng.choice(move_pool)

        # Greedy: pick move with highest Q-value inside move_pool
        best_move = move_pool[0]
        best_q = self.q_value(board, stone, best_move)
        for move in move_pool[1:]:
            q = self.q_value(board, stone, move)
            if q > best_q:
                best_q = q
                best_move = move
        return best_move

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
            self.weights[k] = new_w