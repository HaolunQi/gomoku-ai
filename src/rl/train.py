# rl/train.py
import json
import os
import random

# TODO: fix import path if needed
try:
    from agents.rl_agent import RLAgent
except Exception:
    RLAgent = None


def save_weights(path, weights):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)


def load_weights(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def train_self_play(
    out_path="weights_rl.json",
    episodes=10,
    seed=0,
):
    # Self-play training skeleton.
    #
    # TODO: implement:
    #   - small board restriction (e.g., size <= 7)
    #   - self-play rollouts using Board + rules
    #   - reward shaping (win/loss at terminal)
    #   - Q-learning updates on transitions
    #
    # Placeholder: just writes a minimal weights file that RLAgent can load.

    rng = random.Random(seed)
    weights = {
        # TODO: align with heuristics/features.py feature names
        "my_stones": rng.uniform(-0.1, 0.1),
        "opp_stones": rng.uniform(-0.1, 0.1),
        "empty": 0.0,
    }
    save_weights(out_path, weights)
    return weights


if __name__ == "__main__":
    train_self_play()
