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
    "my_live_two": 10.0,
    "my_blocked_two": 5.0,
    "my_live_three": 120.0,
    "my_blocked_three": 40.0,
    "my_live_four": 10000.0,
    "my_blocked_four": 1000.0,

    "opp_live_two": -20.0,
    "opp_blocked_two": -10.0,
    "opp_live_three": -400.0,
    "opp_blocked_three": -120.0,
    "opp_live_four": -50000.0,
    "opp_blocked_four": -15000.0,

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
    # TODO: add rule-based overrides (immediate win/lose detection) in a safe, minimal way
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
    # TODO: implement cheap heuristics:
    #   - prefer center
    #   - prefer moves near existing stones
    #   - try immediate win/block first (can reuse rules.winner on b.copy())
    if not moves:
        return []

    opp = _other(stone)
    center = (board.size // 2, board.size // 2)

    current_feats = extract_features(board, stone)

    winning_moves = []
    blocking_moves = []
    scored_moves = []

    for move in moves:
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

        # 4) Defensive priority:
        # reward moves that reduce dangerous opponent threats
        threat_reduction = 0.0
        threat_reduction += 50000.0 * (
            current_feats.get("opp_live_four", 0.0) - new_feats.get("opp_live_four", 0.0)
        )
        threat_reduction += 20000.0 * (
            current_feats.get("opp_blocked_four", 0.0) - new_feats.get("opp_blocked_four", 0.0)
        )
        threat_reduction += 8000.0 * (
            current_feats.get("opp_double_blocked_four", 0.0) - new_feats.get("opp_double_blocked_four", 0.0)
        )
        threat_reduction += 6000.0 * (
            current_feats.get("opp_four_and_live_three", 0.0) - new_feats.get("opp_four_and_live_three", 0.0)
        )
        threat_reduction += 4000.0 * (
            current_feats.get("opp_double_live_three", 0.0) - new_feats.get("opp_double_live_three", 0.0)
        )
        threat_reduction += 1200.0 * (
            current_feats.get("opp_live_three", 0.0) - new_feats.get("opp_live_three", 0.0)
        )
        threat_reduction += 300.0 * (
            current_feats.get("opp_blocked_three", 0.0) - new_feats.get("opp_blocked_three", 0.0)
        )

        # Small center tie-break
        dist = abs(move[0] - center[0]) + abs(move[1] - center[1])

        # Larger is better
        priority = threat_reduction + val
        scored_moves.append((move, priority, dist))

    winning_moves.sort(key=lambda m: (m[0], m[1]))
    blocking_moves.sort(key=lambda m: (m[0], m[1]))
    scored_moves.sort(key=lambda x: (-x[1], x[2], x[0][0], x[0][1]))

    return winning_moves + blocking_moves + [move for move, _, _ in scored_moves]


def load_weights_json(path):
    # TODO: standardize weight file schema (version, feature list) if needed
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights_json(path, weights):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)