# heuristics/evaluate.py
import json

from gomoku import rules

try:
    from heuristics.features import extract_features
except ImportError:
    def extract_features(board, stone):
        return {"bias": 1.0}


<<<<<<< HEAD
BASE_PATTERN_WEIGHTS = {
    "stones": 1.0,
    "empty": 0.0,

    # small shapes
    "live_two": 2.0,
    "blocked_two": 0.5,

    # threes
    "live_three": 20.0,
    "blocked_three": 4.0,
    "jump_three": 12.0,
    "blocked_jump_three": 2.0,

    # fours
    "live_four": 1000.0,
    "blocked_four": 15.0,
    "jump_four": 120.0,
    "blocked_jump_four": 10.0,

    # forcing structures
    "double_live_three": 200.0,
    "double_jump_three": 80.0,
    "jump3_and_live3": 250.0,

    "double_blocked_four": 120.0,
    "blocked4_and_jump4": 300.0,
    "blocked4_and_live3": 400.0,

    # compatibility
    "four_and_live_three": 500.0,
=======
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
>>>>>>> d37498d (Add training loop with evaluation)
}

WIN_SCORE = 1_000_000.0
LOSS_SCORE = -1_000_000.0


EDGE_BLOCK_THREE_PENALTY = 100000.0


def _other(stone):
    return "O" if stone == "X" else "X"

def _build_mirror_weights(base):
    w = {}

    # symmetric base features
    w["my_stones"] = base["stones"]
    w["opp_stones"] = -base["stones"]
    w["empty"] = base["empty"]

    for k, v in base.items():
        if k in ("stones", "empty"):
            continue
        w[f"my_{k}"] = v
        w[f"opp_{k}"] = -v

    w["bias"] = 0.0
    return w


DEFAULT_WEIGHTS = _build_mirror_weights(BASE_PATTERN_WEIGHTS)


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

    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    opp = _other(stone)
    center = (board.size // 2, board.size // 2)
    before_eval = evaluate(board, stone, weights=w)
    before_feats = extract_features(board, stone)

    winning_moves = []
    blocking_moves = []
    forced_defense_moves = []
    scored_moves = []

    opp_three_pressure = (
        before_feats.get("opp_live_three", 0.0)
        + before_feats.get("opp_jump_three", 0.0)
    )

    my_attack_ready = (
        before_feats.get("my_live_three", 0.0) > 0.0
        or before_feats.get("my_jump_three", 0.0) > 0.0
        or before_feats.get("my_live_four", 0.0) > 0.0
        or before_feats.get("my_jump_four", 0.0) > 0.0
    )

    must_defend = (opp_three_pressure > 0.0 and not my_attack_ready)

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

        after_eval = evaluate(next_board, stone, weights=w)
        after_feats = extract_features(next_board, stone)
        delta = after_eval - before_eval

        r, c = move
        dist = abs(r - center[0]) + abs(c - center[1])

        # --- forced defense branch ---
        if must_defend:
            jump4_red = (
                before_feats.get("opp_jump_four", 0.0)
                - after_feats.get("opp_jump_four", 0.0)
            )
            live3_red = (
                before_feats.get("opp_live_three", 0.0)
                - after_feats.get("opp_live_three", 0.0)
            )
            jump3_red = (
                before_feats.get("opp_jump_three", 0.0)
                - after_feats.get("opp_jump_three", 0.0)
            )
            three_reduction = jump4_red + live3_red + jump3_red

            if three_reduction > 0.0:
                forced_defense_moves.append(
                    (move, three_reduction, live3_red, jump3_red, delta, dist)
                )
                continue

        # --- offensive shape deltas ---
        new_live_four = after_feats.get("my_live_four", 0.0) - before_feats.get("my_live_four", 0.0)
        new_jump_four = after_feats.get("my_jump_four", 0.0) - before_feats.get("my_jump_four", 0.0)
        new_blocked_four = after_feats.get("my_blocked_four", 0.0) - before_feats.get("my_blocked_four", 0.0)

        new_live_three = after_feats.get("my_live_three", 0.0) - before_feats.get("my_live_three", 0.0)
        new_jump_three = after_feats.get("my_jump_three", 0.0) - before_feats.get("my_jump_three", 0.0)
        new_blocked_three = after_feats.get("my_blocked_three", 0.0) - before_feats.get("my_blocked_three", 0.0)

        new_blocked4_and_live3 = after_feats.get("my_blocked4_and_live3", 0.0) - before_feats.get("my_blocked4_and_live3", 0.0)
        new_blocked4_and_jump3 = after_feats.get("my_blocked4_and_jump3", 0.0) - before_feats.get("my_blocked4_and_jump3", 0.0)

        new_double_live_three = after_feats.get("my_double_live_three", 0.0) - before_feats.get("my_double_live_three", 0.0)
        new_double_jump_three = after_feats.get("my_double_jump_three", 0.0) - before_feats.get("my_double_jump_three", 0.0)
        new_jump3_and_live3 = after_feats.get("my_jump3_and_live3", 0.0) - before_feats.get("my_jump3_and_live3", 0.0)
        

        # key idea:
        # prefer "clean live three" over jump-three-based growth
        attack_key = (
            new_live_four > 0.0,
            new_jump_four > 0.0,
            new_blocked_four > 0.0,
            new_live_three > 0.0,
            new_jump_three > 0.0,  
            new_blocked_three > 0.0, 
            new_double_live_three > 0.0,
            new_jump3_and_live3 > 0.0,
            new_double_jump_three > 0.0,  
            new_blocked4_and_live3 > 0.0,
            new_blocked4_and_jump3 > 0.0,              
        )

        scored_moves.append(
            (
                move,
                attack_key,
                delta,
                dist,
                new_live_four,
                new_jump_four,
                new_blocked_four,
                new_live_three,
                new_jump_three,
                new_blocked_three,
                new_double_live_three,
                new_jump3_and_live3,
                new_double_jump_three,
                new_blocked4_and_live3,
                new_blocked4_and_jump3,
            )
        )

    winning_moves.sort(key=lambda m: (m[0], m[1]))
    blocking_moves.sort(key=lambda m: (m[0], m[1]))

    forced_defense_moves.sort(
        key=lambda x: (-x[1], -x[2], -x[3], -x[4], x[5], x[0][0], x[0][1])
    )

    # lexicographic attack priority first, eval second
    scored_moves.sort(
        key=lambda x: (
            -int(x[1][0]),   # live four
            -int(x[1][1]),   # jump four
            -int(x[1][2]),   # blocked four
            -int(x[1][3]),   # live three
            -int(x[1][4]),   # jump three
            -int(x[1][5]),   # blocked three
            -int(x[1][6]),   # double live three
            -int(x[1][7]),   # jump3 + live3
            -int(x[1][8]),   # double jump three
            -int(x[1][9]),   # blocked4 + live3
            -int(x[1][10]),  # blocked4 + jump3
            -x[2],           # delta
            x[3],            # dist
            x[0][0],
            x[0][1],
        )
    )

    if forced_defense_moves:
        return (
            winning_moves
            + blocking_moves
            + [move for move, *_ in forced_defense_moves]
            + [x[0] for x in scored_moves]
        )

    return winning_moves + blocking_moves + [x[0] for x in scored_moves]

def debug_evaluate(board, stone, weights=None):
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    opp = _other(stone)
    winner = rules.winner(board.grid)

    print(f"=== debug_evaluate for stone={stone} ===")

    if winner == stone:
        print(f"Terminal winner: {stone}")
        print(f"score = {WIN_SCORE}")
        return WIN_SCORE

    if winner == opp:
        print(f"Terminal winner: {opp}")
        print(f"score = {LOSS_SCORE}")
        return LOSS_SCORE

    feats = extract_features(board, stone)
    total = 0.0

    print("Features:")
    for k in sorted(feats.keys()):
        v = float(feats[k])
        wk = float(w.get(k, 0.0))
        contrib = wk * v
        total += contrib
        print(
            f"  {k:>24}: value={v:<8.3f} "
            f"weight={wk:<10.3f} contrib={contrib:<10.3f}"
        )

    print(f"Total score = {total}")
    return float(total)

def debug_order_moves(board, moves, stone, weights=None, top_k=None):
    if not moves:
        print("No moves.")
        return []

    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    opp = _other(stone)
    center = (board.size // 2, board.size // 2)
    before_eval = evaluate(board, stone, weights=w)
    before_feats = extract_features(board, stone)

    must_block_opp_live_three = (
        before_feats.get("opp_live_three", 0.0) > 0.0
        and before_feats.get("my_live_three", 0.0) <= 0.0
        and before_feats.get("my_jump_three", 0.0) <= 0.0
        and before_feats.get("my_live_four", 0.0) <= 0.0
        and before_feats.get("my_jump_four", 0.0) <= 0.0
    )

    rows = []

    for move in moves:
        r, c = move
        dist = abs(r - center[0]) + abs(c - center[1])

        row = {
            "move": move,
            "tag": "normal",
            "before_eval": before_eval,
            "after_eval": None,
            "delta": None,
            "priority": None,
            "dist": dist,
            "opp_live_three_reduction": 0.0,
        }

        if _is_immediate_win(board, move, stone):
            row["tag"] = "immediate_win"
            row["priority"] = float("inf")
            rows.append(row)
            continue

        if _is_immediate_block(board, move, opp):
            row["tag"] = "immediate_block"
            row["priority"] = float("inf")
            rows.append(row)
            continue

        next_board = _simulate_move(board, move, stone)
        if next_board is None:
            row["tag"] = "illegal"
            row["priority"] = float("-inf")
            rows.append(row)
            continue

        after_eval = evaluate(next_board, stone, weights=w)
        delta = after_eval - before_eval

        row["after_eval"] = after_eval
        row["delta"] = delta
        row["priority"] = delta

        if must_block_opp_live_three:
            after_feats = extract_features(next_board, stone)
            opp_live_three_reduction = (
                before_feats.get("opp_live_three", 0.0)
                - after_feats.get("opp_live_three", 0.0)
            )
            row["opp_live_three_reduction"] = opp_live_three_reduction
            if opp_live_three_reduction > 0.0:
                row["tag"] = "forced_block_live_three"
                row["priority"] = 1_000_000.0 + opp_live_three_reduction * 1000.0 + delta

        rows.append(row)

    def sort_key(x):
        if x["tag"] == "immediate_win":
            return (0, 0, 0, x["move"][0], x["move"][1])
        if x["tag"] == "immediate_block":
            return (1, 0, 0, x["move"][0], x["move"][1])
        if x["tag"] == "forced_block_live_three":
            return (2, -x["opp_live_three_reduction"], -x["delta"], x["dist"], x["move"][0], x["move"][1])
        return (3, -x["priority"], x["dist"], x["move"][0], x["move"][1])

    rows.sort(key=sort_key)

    if top_k is not None:
        rows = rows[:top_k]

    print(f"=== debug_order_moves for stone={stone} ===")
    print(f"before_eval={before_eval}")
    print(f"must_block_opp_live_three={must_block_opp_live_three}")
    for i, row in enumerate(rows, 1):
        print(
            f"{i:2d}. move={row['move']} "
            f"priority={row['priority']} "
            f"after={row['after_eval']} "
            f"delta={row['delta']} "
            f"dist={row['dist']}"
        )

    return rows


def load_weights_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights_json(path, weights):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)