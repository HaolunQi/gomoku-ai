# heuristics/evaluate.py
import json

from gomoku import rules

# TODO: fix import path if needed
try:
    from heuristics.features import extract_features
except Exception:
    def extract_features(board, stone):
        return {"bias": 1.0}


# Default weights kept small and explicit
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


def _other(stone):
    return "O" if stone == "X" else "X"


def evaluate(board, stone, weights=None):
    # Linear evaluation: sum_i w_i * f_i
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    opp = _other(stone)

    # Rule-based overrides: terminal win/loss should dominate heuristic score
    winner = rules.winner(board.grid)
    if winner == stone:
        return WIN_SCORE
    if winner == opp:
        return LOSS_SCORE

    feats = extract_features(board, stone)
    score = 0.0
    for k, v in feats.items():
        score += float(w.get(k, 0.0)) * float(v)
    return float(score)


def order_moves(board, moves, stone, weights=None):
    # Move ordering hook for AB (and optionally RL)
    if not moves:
        return []

    opp = _other(stone)
    center = (board.size // 2, board.size // 2)

    current_feats = extract_features(board, stone)

    winning_moves = []
    blocking_moves = []
    scored_moves = []

    for move in moves:
        r, c = move
        on_edge = (r == 0 or r == board.size - 1 or c == 0 or c == board.size - 1)

        # 1) Immediate winning move for current player
        b1 = board.copy()
        if b1.place(move, stone) and rules.winner(b1.grid) == stone:
            winning_moves.append(move)
            continue

        # 2) Immediate blocking move against opponent win
        b2 = board.copy()
        if b2.place(move, opp) and rules.winner(b2.grid) == opp:
            blocking_moves.append(move)
            continue

        # 3) Static evaluation after move
        b3 = board.copy()
        ok = b3.place(move, stone)
        if not ok:
            continue

        val = evaluate(b3, stone, weights)
        new_feats = extract_features(b3, stone)

        # 4) Threat reductions
        reduce_opp_live_four = current_feats.get("opp_live_four", 0.0) - new_feats.get("opp_live_four", 0.0)
        reduce_opp_jump_four = current_feats.get("opp_jump_four", 0.0) - new_feats.get("opp_jump_four", 0.0)
        reduce_opp_blocked_four = current_feats.get("opp_blocked_four", 0.0) - new_feats.get("opp_blocked_four", 0.0)
        reduce_opp_double_blocked_four = current_feats.get("opp_double_blocked_four", 0.0) - new_feats.get("opp_double_blocked_four", 0.0)
        reduce_opp_four_and_live_three = current_feats.get("opp_four_and_live_three", 0.0) - new_feats.get("opp_four_and_live_three", 0.0)
        reduce_opp_double_live_three = current_feats.get("opp_double_live_three", 0.0) - new_feats.get("opp_double_live_three", 0.0)
        reduce_opp_jump_three = current_feats.get("opp_jump_three", 0.0) - new_feats.get("opp_jump_three", 0.0)
        reduce_opp_live_three = current_feats.get("opp_live_three", 0.0) - new_feats.get("opp_live_three", 0.0)
        reduce_opp_blocked_three = current_feats.get("opp_blocked_three", 0.0) - new_feats.get("opp_blocked_three", 0.0)

        threat_reduction = 0.0
        threat_reduction += 50000.0 * reduce_opp_live_four
        threat_reduction += 30000.0 * reduce_opp_jump_four
        threat_reduction += 20000.0 * reduce_opp_blocked_four
        threat_reduction += 8000.0 * reduce_opp_double_blocked_four
        threat_reduction += 6000.0 * reduce_opp_four_and_live_three
        threat_reduction += 4000.0 * reduce_opp_double_live_three
        threat_reduction += 2500.0 * reduce_opp_jump_three
        threat_reduction += 1200.0 * reduce_opp_live_three
        threat_reduction += 300.0 * reduce_opp_blocked_three

        # 5) My own attack gain
        my_attack_gain = 0.0
        my_attack_gain += 20000.0 * (new_feats.get("my_live_four", 0.0) - current_feats.get("my_live_four", 0.0))
        my_attack_gain += 8000.0 * (new_feats.get("my_blocked_four", 0.0) - current_feats.get("my_blocked_four", 0.0))
        my_attack_gain += 2500.0 * (new_feats.get("my_double_live_three", 0.0) - current_feats.get("my_double_live_three", 0.0))
        my_attack_gain += 1200.0 * (new_feats.get("my_live_three", 0.0) - current_feats.get("my_live_three", 0.0))
        my_attack_gain += 600.0 * (new_feats.get("my_jump_three", 0.0) - current_feats.get("my_jump_three", 0.0))

        # 6) On-edge anti-"block three" rule:
        # If the move is on the edge, do not reward it merely for blocking 3-type threats.
        strong_defense_gain = 0.0
        strong_defense_gain += 50000.0 * reduce_opp_live_four
        strong_defense_gain += 30000.0 * reduce_opp_jump_four
        strong_defense_gain += 20000.0 * reduce_opp_blocked_four
        strong_defense_gain += 8000.0 * reduce_opp_double_blocked_four
        strong_defense_gain += 6000.0 * reduce_opp_four_and_live_three
        strong_defense_gain += 4000.0 * reduce_opp_double_live_three

        weak_three_defense_gain = 0.0
        weak_three_defense_gain += 2500.0 * reduce_opp_jump_three
        weak_three_defense_gain += 1200.0 * reduce_opp_live_three
        weak_three_defense_gain += 300.0 * reduce_opp_blocked_three

        edge_penalty = 0.0
        if on_edge:
            # Edge move is allowed only if:
            # - it creates real attack, or
            # - it handles strong threats (4s / double threats)
            # Otherwise, if it mainly blocks 3s, suppress it.
            if strong_defense_gain <= 0.0 and my_attack_gain <= 0.0 and weak_three_defense_gain > 0.0:
                edge_penalty -= 100000.0

        # Small center tie-break
        dist = abs(r - center[0]) + abs(c - center[1])

        # Larger is better
        priority = threat_reduction + val + edge_penalty
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