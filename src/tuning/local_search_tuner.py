# tuning/local_search_tuner.py
import json
import os
import random

try:
    from tuning.objective import objective
except Exception:
    def objective(weights, board_factory, opponents, games=4, time_penalty_weight=0.001):
        return 0.0


class LocalSearchTuner:
    # First-choice hill climbing with random restarts.
    # Each restart does iters steps; we keep the best weights found across all runs.

    def __init__(self, rng_seed=0):
        self._rng = random.Random(rng_seed)

    def random_weights(self, feature_names):
        # start from a random point in [-1, 1] for each feature
        return {k: self._rng.uniform(-1.0, 1.0) for k in feature_names}

    def perturb(self, weights, step=0.1):
        # nudge one randomly chosen weight by a small amount
        w2 = dict(weights)
        if not w2:
            return w2
        k = self._rng.choice(list(w2.keys()))
        w2[k] = float(w2[k]) + self._rng.uniform(-step, step)
        return w2

    def tune(
        self,
        initial_weights,
        board_factory,
        opponents,
        out_path,
        iters=50,
        restarts=2,
        games=4,
        time_penalty_weight=0.001,
    ):
        feature_names = list((initial_weights or {}).keys())

        # track the best weights found across all restarts
        best = dict(initial_weights or {})
        best_score = objective(best, board_factory, opponents, games=games, time_penalty_weight=time_penalty_weight)

        for restart_idx in range(restarts + 1):
            # first run uses initial_weights; subsequent runs jump to a random start
            if restart_idx == 0:
                current = dict(best)
            else:
                current = self.random_weights(feature_names) if feature_names else {}

            current_score = objective(current, board_factory, opponents, games=games, time_penalty_weight=time_penalty_weight)

            # first-choice hill climbing: accept the first neighbor that improves the score
            for _ in range(max(0, int(iters))):
                cand = self.perturb(current, step=0.1)
                cand_score = objective(cand, board_factory, opponents, games=games, time_penalty_weight=time_penalty_weight)
                if cand_score > current_score:
                    current, current_score = cand, cand_score

            if current_score > best_score:
                best, best_score = current, current_score

        self.save(out_path, best)
        return best

    def save(self, path, weights):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=2, sort_keys=True)

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
