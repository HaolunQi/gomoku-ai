# tuning/local_search_tuner.py
import json
import os
import random

# TODO: fix import path if needed
try:
    from tuning.objective import objective
except Exception:
    def objective(weights, board_factory, opponents, games=4, time_penalty_weight=0.001):
        return 0.0


class LocalSearchTuner:
    # First-choice hill climbing / random-restart skeleton
    #
    # TODO: implements:
    #   - neighbor generation (perturb weights)
    #   - first-choice loop (accept first improving neighbor)
    #   - random restarts (track best overall)
    #   - save best weights to json

    def __init__(self, rng_seed=0):
        self._rng = random.Random(rng_seed)

    def random_weights(self, feature_names):
        # TODO: define a sensible init distribution
        return {k: self._rng.uniform(-1.0, 1.0) for k in feature_names}

    def perturb(self, weights, step=0.1):
        # TODO: create a neighbor (small random changes)
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
        # TODO: implement full tuning loop; keep placeholder runnable and writing file

        best = dict(initial_weights or {})
        best_score = objective(best, board_factory, opponents, games=games, time_penalty_weight=time_penalty_weight)

        # Placeholder: do a tiny number of safe perturbations (NOT real algorithm)
        for _ in range(max(0, int(iters))):
            cand = self.perturb(best, step=0.0)  # step=0 keeps behavior stable
            cand_score = objective(cand, board_factory, opponents, games=games, time_penalty_weight=time_penalty_weight)
            if cand_score > best_score:
                best, best_score = cand, cand_score

        self.save(out_path, best)
        return best

    def save(self, path, weights):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=2, sort_keys=True)

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
