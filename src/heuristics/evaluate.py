# heuristics/evaluate.py
import json

# TODO: fix import path if needed
try:
    from heuristics.features import extract_features
except Exception:
    def extract_features(board, stone):
        return {"bias": 1.0}


# Default weights — hand-tuned baseline (overridden by learned RL weights)
DEFAULT_WEIGHTS = {
    "bias": 0.0,
    "my_open_four": 100.0,
    "my_half_four": 50.0,
    "my_open_three": 20.0,
    "my_half_three": 5.0,
    "my_open_two": 2.0,
    "opp_open_four": -100.0,
    "opp_half_four": -50.0,
    "opp_open_three": -20.0,
    "opp_half_three": -5.0,
    "opp_open_two": -2.0,
    "my_stones": 0.1,
    "center_control": -1.0,
}


def evaluate(board, stone, weights=None):
    # Linear evaluation: sum_i w_i * f_i
    # TODO: add rule-based overrides (immediate win/lose detection) in a safe, minimal way
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    feats = extract_features(board, stone)
    score = 0.0
    for k, v in feats.items():
        score += float(w.get(k, 0.0)) * float(v)
    return float(score)


def order_moves(board, moves, stone, weights=None):
    # Move ordering hook for AB (and optionally RL)
    # TODO: implement cheap heuristics:
    #   - prefer center
    #   - prefer moves near existing stones
    #   - try immediate win/block first (can reuse rules.winner on b.copy())
    if not moves:
        return []

    center = (board.size // 2, board.size // 2)

    def key(m):
        # Deterministic, cheap
        return (abs(m[0] - center[0]) + abs(m[1] - center[1]), m[0], m[1])

    return sorted(list(moves), key=key)


def load_weights_json(path):
    # TODO: standardize weight file schema (version, feature list) if needed
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights_json(path, weights):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)
