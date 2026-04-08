import random
from agents.base import Agent
from gomoku import rules
from heuristics.features import extract_features, featurize_after_move


class RLAgent(Agent):
    name = "rl"

    def __init__(self, weights=None, alpha=0.01, gamma=0.99, epsilon=0.1, seed=0):
        # linear Q params + epsilon-greedy
        self.weights = dict(weights or {})
        self.alpha = float(alpha)
        self.gamma = float(gamma)
        self.epsilon = float(epsilon)
        self._rng = random.Random(seed)

    def select_move(self, board, stone):
        # epsilon-greedy with win check
        moves = board.candidate_moves()
        if not moves:
            raise RuntimeError("Candiate legal moves available (game is over).")

        # take immediate win
        for move in moves:
            b = board.copy()
            if b.place(move, stone) and rules.winner(b.grid) == stone:
                return move

        # explore
        if self._rng.random() < self.epsilon:
            return self._rng.choice(moves)

        # exploit: max Q
        best_move = moves[0]
        best_q = None
        for move in moves:
            q = self.q_value(board, stone, move)
            if best_q is None or q > best_q:
                best_q = q
                best_move = move
        return best_move

    def q_value(self, board, stone, move):
        # linear Q(s,a) with heuristic shaping
        before = extract_features(board, stone)
        after = featurize_after_move(board, stone, move)

        q = 0.0
        for k, v in after.items():
            q += float(self.weights.get(k, 0.0)) * float(v)

        # opponent threat reduction
        before_opp_three = (
            before.get("opp_live_three", 0.0)
            + before.get("opp_jump_three", 0.0)
        )
        after_opp_three = (
            after.get("opp_live_three", 0.0)
            + after.get("opp_jump_three", 0.0)
        )

        before_opp_four = (
            before.get("opp_live_four", 0.0)
            + before.get("opp_jump_four", 0.0)
            + before.get("opp_blocked_four", 0.0)
        )
        after_opp_four = (
            after.get("opp_live_four", 0.0)
            + after.get("opp_jump_four", 0.0)
            + after.get("opp_blocked_four", 0.0)
        )

        # my attack strength
        after_my_attack = (
            after.get("my_live_three", 0.0)
            + after.get("my_jump_three", 0.0)
            + after.get("my_live_four", 0.0)
            + after.get("my_blocked_four", 0.0)
            + after.get("my_jump_four", 0.0)
        )

        # reward blocking threats
        q += 60.0 * (before_opp_three - after_opp_three)
        q += 180.0 * (before_opp_four - after_opp_four)

        # penalize ignoring threats
        if before_opp_three > 0.0 and after_opp_three >= before_opp_three and after_my_attack > 0.0:
            q -= 45.0

        if before_opp_four > 0.0 and after_opp_four > 0.0:
            q -= 160.0

        return float(q)

    def best_q(self, board, stone):
        # max Q over actions
        moves = board.candidate_moves()
        if not moves:
            return 0.0
        return max(self.q_value(board, stone, m) for m in moves)

    def update(self, board, stone, move, reward, next_board, next_stone, done):
        # Q-learning update (linear approx)
        feats = featurize_after_move(board, stone, move)

        current_q = 0.0
        for k, v in feats.items():
            current_q += float(self.weights.get(k, 0.0)) * float(v)

        if done:
            target = reward
        else:
            target = reward + self.gamma * self.best_q(next_board, next_stone)

        error = target - current_q
        error = max(-10.0, min(10.0, error))

        for k, v in feats.items():
            fv = float(v)
            if fv == 0.0:
                continue
            old_w = float(self.weights.get(k, 0.0))
            self.weights[k] = old_w + self.alpha * error * fv