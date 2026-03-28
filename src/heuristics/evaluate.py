# heuristics/evaluate.py
import json

from gomoku import rules

try:
    from heuristics.features import extract_features
except ImportError:
    def extract_features(board, stone):
        return {"bias": 1.0}


DEFAULT_WEIGHTS = {
    "my_stones": 1.0,
    "opp_stones": -1.0,
    "empty": 0.0,

    "my_live_two": 10.0,
    "my_blocked_two": 5.0,
    "my_live_three": 120.0,
    "my_blocked_three": 40.0,
    "my_live_four": 10000.0,
    "my_blocked_four": 1000.0,
    "my_jump_three": 0.0,
    "my_jump_four": 0.0,

    "opp_live_two": -20.0,
    "opp_blocked_two": -10.0,
    "opp_live_three": -400.0,
    "opp_blocked_three": -120.0,
    "opp_live_four": -50000.0,
    "opp_blocked_four": -15000.0,
    "opp_jump_three": -1200.0,
    "opp_jump_four": -45000.0,

    "my_double_live_three": 2500.0,
    "opp_double_live_three": -20000.0,

    "my_double_blocked_four": 9000.0,
    "opp_double_blocked_four": -40000.0,

    "my_four_and_live_three": 8000.0,
    "opp_four_and_live_three": -30000.0,

    "bias": 0.0,
}

WIN_SCORE = 1_000_000.0
LOSS_SCORE = -1_000_000.0

# Move-order-specific weights
DEFENSE_WEIGHTS = {
    "opp_live_four": 50000.0,
    "opp_jump_four": 30000.0,
    "opp_blocked_four": 20000.0,
    "opp_double_blocked_four": 8000.0,
    "opp_four_and_live_three": 6000.0,
    "opp_double_live_three": 4000.0,
    "opp_jump_three": 2500.0,
    "opp_live_three": 1200.0,
    "opp_blocked_three": 300.0,
}

STRONG_DEFENSE_KEYS = {
    "opp_live_four",
    "opp_jump_four",
    "opp_blocked_four",
    "opp_double_blocked_four",
    "opp_four_and_live_three",
    "opp_double_live_three",
}

WEAK_DEFENSE_KEYS = {
    "opp_jump_three",
    "opp_live_three",
    "opp_blocked_three",
}

ATTACK_WEIGHTS = {
    "my_live_four": 20000.0,
    "my_blocked_four": 8000.0,
    "my_double_live_three": 2500.0,
    "my_live_three": 1200.0,
    "my_jump_three": 600.0,
}

EDGE_BLOCK_THREE_PENALTY = 100000.0


def _other(stone):
    return "O" if stone == "X" else "X"


def evaluate(board, stone, weights=None):
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    opp = _other(stone)

    winner = rules.winner(board.grid)
    if winner == stone:
        return WIN_SCORE
    if winner == opp:
        return LOSS_SCORE

    feats = extract_features(board, stone)
    return float(sum(float(w.get(k, 0.0)) * float(v) for k, v in feats.items()))


def _feature_delta(before, after, key):
    return after.get(key, 0.0) - before.get(key, 0.0)


def _weighted_delta_sum(before, after, weights, positive_for_reduction=False, keys=None):
    total = 0.0
    active_keys = keys if keys is not None else weights.keys()

    for key in active_keys:
        if positive_for_reduction:
            delta = before.get(key, 0.0) - after.get(key, 0.0)
        else:
            delta = after.get(key, 0.0) - before.get(key, 0.0)
        total += weights[key] * delta

    return total


def _is_immediate_win(board, move, stone):
    b = board.copy()
    if not b.place(move, stone):
        return False
    return rules.winner(b.grid) == stone


def _is_immediate_block(board, move, opp):
    b = board.copy()
    if not b.place(move, opp):
        return False
    return rules.winner(b.grid) == opp


def _simulate_move(board, move, stone):
    b = board.copy()
    if not b.place(move, stone):
        return None
    return b


def _edge_penalty(move, board_size, strong_defense_gain, weak_defense_gain, my_attack_gain):
    r, c = move
    on_edge = (r == 0 or r == board_size - 1 or c == 0 or c == board_size - 1)
    if not on_edge:
        return 0.0

    if strong_defense_gain <= 0.0 and my_attack_gain <= 0.0 and weak_defense_gain > 0.0:
        return -EDGE_BLOCK_THREE_PENALTY
    return 0.0


def order_moves(board, moves, stone, weights=None):
    if not moves:
        return []

    opp = _other(stone)
    center = (board.size // 2, board.size // 2)
    current_feats = extract_features(board, stone)

    winning_moves = []
    blocking_moves = []
    scored_moves = []

    for move in moves:
        if _is_immediate_win(board, move, stone):
            winning_moves.append(move)
            continue

        if _is_immediate_block(board, move, opp):
            blocking_moves.append(move)
            continue

        next_board = _simulate_move(board, move, stone)
        if next_board is None:
            continue

        new_feats = extract_features(next_board, stone)
        static_eval = evaluate(next_board, stone, weights)

        threat_reduction = _weighted_delta_sum(
            current_feats,
            new_feats,
            DEFENSE_WEIGHTS,
            positive_for_reduction=True,
        )

        strong_defense_gain = _weighted_delta_sum(
            current_feats,
            new_feats,
            DEFENSE_WEIGHTS,
            positive_for_reduction=True,
            keys=STRONG_DEFENSE_KEYS,
        )

        weak_defense_gain = _weighted_delta_sum(
            current_feats,
            new_feats,
            DEFENSE_WEIGHTS,
            positive_for_reduction=True,
            keys=WEAK_DEFENSE_KEYS,
        )

        my_attack_gain = _weighted_delta_sum(
            current_feats,
            new_feats,
            ATTACK_WEIGHTS,
            positive_for_reduction=False,
        )

        penalty = _edge_penalty(
            move,
            board.size,
            strong_defense_gain,
            weak_defense_gain,
            my_attack_gain,
        )

        r, c = move
        dist = abs(r - center[0]) + abs(c - center[1])

        priority = static_eval + threat_reduction + penalty
        scored_moves.append((move, priority, dist))

    winning_moves.sort(key=lambda m: (m[0], m[1]))
    blocking_moves.sort(key=lambda m: (m[0], m[1]))
    scored_moves.sort(key=lambda x: (-x[1], x[2], x[0][0], x[0][1]))

    return winning_moves + blocking_moves + [move for move, _, _ in scored_moves]


def load_weights_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights_json(path, weights):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)