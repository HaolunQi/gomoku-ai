# heuristics/evaluate.py
import json

from gomoku import rules

try:
    from heuristics.features import extract_features
except ImportError:
    def extract_features(board, stone):
        return {"bias": 1.0}


BASE_PATTERN_WEIGHTS = {
    "stones": 1.0,
    "empty": 0.0,

    # small shapes
    "live_two": 200.0,
    "blocked_two": 50.0,

    # threes
    "live_three": 300.0,
    "blocked_three": 250.0,
    "jump_three": 150.0,
    "blocked_jump_three": 100.0,

    # fours
    "live_four": 1000.0,
    "blocked_four": 400.0,
    "jump_four": 300.0,
    "blocked_jump_four": 250.0,

    # forcing structures
    "double_live_three": 1000.0,
    "double_jump_three": 800.0,
    "jump3_and_live3": 1000.0,
    "double_blocked_four": 1000.0,
    "blocked4_and_jump4": 1000.0,
    "blocked4_and_live3": 1000.0,
    "blocked4_and_jump3": 1000.0
}

WIN_SCORE = 1_0000.0
LOSS_SCORE = -1_0000.0


EDGE_BLOCK_THREE_PENALTY = 100.0


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


def _opp_next_creates_combo(board, stone, candidate_moves):
    opp = _other(stone)
    before = extract_features(board, opp)

    for m in candidate_moves:
        b = board.copy()
        if not b.place(m, opp):
            continue

        after = extract_features(b, opp)

        if ((before.get("my_blocked4_and_live3", 0.0) == 0.0 and after.get("my_blocked4_and_live3", 0.0) > 0.0)
            or (before.get("my_blocked4_and_jump4", 0.0) == 0.0 and after.get("my_blocked4_and_jump4", 0.0) > 0.0)
            or (before.get("my_blocked4_and_jump3", 0.0) == 0.0 and after.get("my_blocked4_and_jump3", 0.0) > 0.0)    
        ):
            return True
    return False

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
        or before_feats.get("my_blocked_four", 0.0) > 0.0
        or before_feats.get("my_jump_four", 0.0) > 0.0
    )

    must_defend_three = (opp_three_pressure > 0.0 and not my_attack_ready)

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
        delta = after_eval - before_eval
        after_feats = extract_features(next_board, stone)

        r, c = move
        dist = abs(r - center[0]) + abs(c - center[1])

        new_live_four = after_feats.get("my_live_four", 0.0) - before_feats.get("my_live_four", 0.0)
        new_jump_four = after_feats.get("my_jump_four", 0.0) - before_feats.get("my_jump_four", 0.0)
        new_blocked_four = after_feats.get("my_blocked_four", 0.0) - before_feats.get("my_blocked_four", 0.0)

        new_live_three = after_feats.get("my_live_three", 0.0) - before_feats.get("my_live_three", 0.0)
        new_jump_three = after_feats.get("my_jump_three", 0.0) - before_feats.get("my_jump_three", 0.0)
        new_blocked_three = after_feats.get("my_blocked_three", 0.0) - before_feats.get("my_blocked_three", 0.0)

        new_double_live_three = after_feats.get("my_double_live_three", 0.0) - before_feats.get("my_double_live_three", 0.0)
        new_jump3_and_live3 = after_feats.get("my_jump3_and_live3", 0.0) - before_feats.get("my_jump3_and_live3", 0.0)
        new_double_jump_three = after_feats.get("my_double_jump_three", 0.0) - before_feats.get("my_double_jump_three", 0.0)

        new_blocked4_and_live3 = after_feats.get("my_blocked4_and_live3", 0.0) - before_feats.get("my_blocked4_and_live3", 0.0)
        new_blocked4_and_jump4 = after_feats.get("my_blocked4_and_jump4", 0.0) - before_feats.get("my_blocked4_and_jump4", 0.0)

        attack_key = (
            new_live_four > 0.0,
            new_blocked4_and_jump4 > 0.0,
            new_blocked4_and_live3 > 0.0,
            new_double_live_three > 0.0,
            new_jump3_and_live3 > 0.0,
            new_double_jump_three > 0.0,
            new_jump_four > 0.0,
            new_blocked_four > 0.0,
            new_live_three > 0.0,
            new_jump_three > 0.0,
            new_blocked_three > 0.0,
        )

        scored_moves.append((move, attack_key, delta, dist, next_board))

    scored_moves.sort(
        key=lambda x: (
            -int(x[1][0]),
            -int(x[1][1]),
            -int(x[1][2]),
            -int(x[1][3]),
            -int(x[1][4]),
            -int(x[1][5]),
            -int(x[1][6]),
            -int(x[1][7]),
            -int(x[1][8]),
            -int(x[1][9]),
            -int(x[1][10]),
            -x[2],
            x[3],
            x[0][0],
            x[0][1],
        )
    )

    TOP_K = 10
    for i in range(min(TOP_K, len(scored_moves))):
        move, attack_key, delta, dist, next_board = scored_moves[i]

        # already forcing enough: skip opponent-combo check
        is_strong_forcing = (
            attack_key[0]     # live_four
            or attack_key[1]  # blocked4_and_jump4
            or attack_key[2]  # blocked4_and_live3
        )

        if not is_strong_forcing:
            opp_moves = next_board.candidate_moves(radius=2)
            if _opp_next_creates_combo(next_board, stone, opp_moves):
                delta -= 50000.0

        scored_moves[i] = (move, attack_key, delta, dist, next_board)

    scored_moves.sort(
        key=lambda x: (
            -int(x[1][0]),
            -int(x[1][1]),
            -int(x[1][2]),
            -int(x[1][3]),
            -int(x[1][4]),
            -int(x[1][5]),
            -int(x[1][6]),
            -int(x[1][7]),
            -int(x[1][8]),
            -int(x[1][9]),
            -int(x[1][10]),
            -x[2],
            x[3],
            x[0][0],
            x[0][1],
        )
    )

    if must_defend_three:
        for move, attack_key, delta, dist, next_board in scored_moves:
            after_feats = extract_features(next_board, stone)

            live3_red = (
                before_feats.get("opp_live_three", 0.0)
                - after_feats.get("opp_live_three", 0.0)
            )
            jump3_red = (
                before_feats.get("opp_jump_three", 0.0)
                - after_feats.get("opp_jump_three", 0.0)
            )

            three_reduction = live3_red + jump3_red

            if three_reduction > 0.0:
                forced_defense_moves.append(
                    (move, three_reduction, live3_red, jump3_red, delta, dist)
                )

        forced_defense_moves.sort(
            key=lambda x: (-x[1], -x[2], -x[3], -x[4], x[5], x[0][0], x[0][1])
        )

        if forced_defense_moves:
            forced_set = {move for move, *_ in forced_defense_moves}
            remaining_moves = [move for move, *_ in scored_moves if move not in forced_set]

            return (
                winning_moves
                + blocking_moves
                + [move for move, *_ in forced_defense_moves]
                + remaining_moves
            )

    return winning_moves + blocking_moves + [move for move, *_ in scored_moves]

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

def debug_order_moves(board, moves, stone, weights=None, top_k=10):
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

    def build_attack_key(before, after):
        return (
            after["my_live_four"] > before["my_live_four"],
            after["my_blocked4_and_jump4"] > before["my_blocked4_and_jump4"],
            after["my_blocked4_and_live3"] > before["my_blocked4_and_live3"],
            after["my_double_live_three"] > before["my_double_live_three"],
            after["my_jump3_and_live3"] > before["my_jump3_and_live3"],
            after["my_double_jump_three"] > before["my_double_jump_three"],
            after["my_jump_four"] > before["my_jump_four"],
            after["my_blocked_four"] > before["my_blocked_four"],
            after["my_live_three"] > before["my_live_three"],
            after["my_jump_three"] > before["my_jump_three"],
            after["my_blocked_three"] > before["my_blocked_three"],
        )

    rows = []

    for move in moves:
        r, c = move
        dist = abs(r - center[0]) + abs(c - center[1])

        if _is_immediate_win(board, move, stone):
            rows.append((move, "win", None, None, dist, None, 0.0, 0.0, 0.0))
            continue

        if _is_immediate_block(board, move, opp):
            rows.append((move, "block", None, None, dist, None, 0.0, 0.0, 0.0))
            continue

        next_board = _simulate_move(board, move, stone)
        if next_board is None:
            rows.append((move, "illegal", None, None, dist, None, 0.0, 0.0, 0.0))
            continue

        after_eval = evaluate(next_board, stone, weights=w)
        delta = after_eval - before_eval
        after_feats = extract_features(next_board, stone)

        ak = build_attack_key(before_feats, after_feats)

        is_strong_forcing = (
            ak[0]
            or ak[1]
            or ak[2]
        )

        if is_strong_forcing:
            opp_combo_penalty = 0.0
        else:
            opp_moves = next_board.candidate_moves(radius=2)
            opp_next_combo = _opp_next_creates_combo(next_board, stone, opp_moves)
            opp_combo_penalty = 50000.0 if opp_next_combo else 0.0

        final_delta = delta - opp_combo_penalty

        live3_red = (
            before_feats.get("opp_live_three", 0.0)
            - after_feats.get("opp_live_three", 0.0)
        )
        jump3_red = (
            before_feats.get("opp_jump_three", 0.0)
            - after_feats.get("opp_jump_three", 0.0)
        )
        three_reduction = live3_red + jump3_red

        rows.append((
            move, "normal", ak, final_delta, dist, delta,
            three_reduction, live3_red, jump3_red
        ))

    def normal_key(row):
        move, tag, ak, final_delta, dist, raw_delta, three_reduction, live3_red, jump3_red = row

        if ak is None:
            ak = (False,) * 11

        return (
            *[-int(v) for v in ak],
            -(final_delta if final_delta is not None else -1e18),
            dist,
            move[0],
            move[1],
        )

    win_rows = [r for r in rows if r[1] == "win"]
    block_rows = [r for r in rows if r[1] == "block"]
    illegal_rows = [r for r in rows if r[1] == "illegal"]
    normal_rows = [r for r in rows if r[1] == "normal"]

    normal_rows.sort(key=normal_key)

    if must_defend_three:
        forced_rows = [r for r in normal_rows if r[6] > 0.0]
        remaining_rows = [r for r in normal_rows if r[6] <= 0.0]

        forced_rows.sort(
            key=lambda r: (
                -r[6],   # three_reduction
                -r[7],   # live3_red
                -r[8],   # jump3_red
                -r[3],   # final_delta
                r[4],    # dist
                r[0][0],
                r[0][1],
            )
        )

        rows = win_rows + block_rows + forced_rows + remaining_rows + illegal_rows
    else:
        rows = win_rows + block_rows + normal_rows + illegal_rows

    if top_k is not None:
        rows = rows[:top_k]

    print(f"=== debug_order_moves ({stone}) ===")
    print(f"before_eval={before_eval:.1f}")
    print(f"opp_three_pressure={opp_three_pressure:.1f}")
    print(f"my_attack_ready={my_attack_ready}")
    print(f"must_defend_three={must_defend_three}\n")

    labels = [
        "l4", "b4+j4", "b4+l3", "dbl_l3", "j3+l3",
        "dbl_j3", "j4", "b4", "l3", "j3", "b3"
    ]

    for i, (move, tag, ak, final_delta, dist, raw_delta, three_reduction, live3_red, jump3_red) in enumerate(rows, 1):
        if tag in ("win", "block", "illegal"):
            print(f"{i:2d}. {move} | {tag} | d={dist}")
            continue

        active = [n for n, v in zip(labels, ak) if v]

        print(
            f"{i:2d}. {move} | "
            f"three_red={three_reduction:.1f} "
            f"(l3={live3_red:.1f}, j3={jump3_red:.1f}) | "
            f"atk={active if active else ['-']} | "
            f"Δ={raw_delta:.1f} → {final_delta:.1f} | "
            f"d={dist} |"
        )

    return rows


def load_weights_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights_json(path, weights):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)