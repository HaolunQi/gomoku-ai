import json
from gomoku import rules
from heuristics.features import extract_features


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

    # forcing patterns
    "double_live_three": 1000.0,
    "double_jump_three": 800.0,
    "jump3_and_live3": 1000.0,
    "double_blocked_four": 1000.0,
    "blocked4_and_jump4": 1000.0,
    "blocked4_and_live3": 1000.0,
    "blocked4_and_jump3": 1000.0
}

# terminal scores
WIN_SCORE = 1_0000.0
LOSS_SCORE = -1_0000.0


def _other(stone):
    # return opponent stone
    return "O" if stone == "X" else "X"


def _build_mirror_weights(base):
    # build full weights: my_* positive, opp_* negative
    w = {}
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
    # evaluate board: terminal check + weighted features
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
    # check if move wins immediately
    b = board.copy()
    if not b.place(move, stone):
        return False
    return rules.winner(b.grid) == stone


def _is_immediate_block(board, move, opp):
    # check if move blocks opponent win
    b = board.copy()
    if not b.place(move, opp):
        return False
    return rules.winner(b.grid) == opp


def _simulate_move(board, move, stone):
    # simulate move without modifying original board
    b = board.copy()
    if not b.place(move, stone):
        return None
    return b


def _level_from_feats(feats, prefix):
    # map features to coarse threat level
    if feats.get(f"{prefix}_live_four", 0.0) > 0.0:
        return 6
    if feats.get(f"{prefix}_blocked4_and_live3", 0.0) > 0.0:
        return 5
    if feats.get(f"{prefix}_blocked4_and_jump4", 0.0) > 0.0:
        return 5
    if feats.get(f"{prefix}_double_jump_four", 0.0) > 0.0:
        return 5
    if feats.get(f"{prefix}_double_live_three", 0.0) > 0.0:
        return 4
    if feats.get(f"{prefix}_jump3_and_live3", 0.0) > 0.0:
        return 4
    if feats.get(f"{prefix}_double_jump_three", 0.0) > 0.0:
        return 3
    if feats.get(f"{prefix}_live_three", 0.0) > 0.0:
        return 2
    if feats.get(f"{prefix}_jump_three", 0.0) > 0.0:
        return 1
    return 0


# features used for attack delta
_ATTACK_DELTA_KEYS = [
    "my_live_four",
    "my_jump_four",
    "my_blocked_four",
    "my_live_three",
    "my_jump_three",
    "my_blocked_three",
    "my_double_live_three",
    "my_jump3_and_live3",
    "my_double_jump_three",
    "my_blocked4_and_live3",
    "my_blocked4_and_jump4",
    "my_double_jump_four",
]


def _feature_deltas(before_feats, after_feats):
    # compute feature changes after move
    return {
        k: after_feats.get(k, 0.0) - before_feats.get(k, 0.0)
        for k in _ATTACK_DELTA_KEYS
    }


def _attack_tier_from_deltas(d):
    # coarse attack priority
    if d["my_live_four"] > 0.0:
        return 5
    if (
        d["my_blocked4_and_jump4"] > 0.0
        or d["my_double_jump_four"] > 0.0
        or d["my_blocked4_and_live3"] > 0.0
    ):
        return 4
    if (
        d["my_double_live_three"] > 0.0
        or d["my_jump3_and_live3"] > 0.0
        or d["my_double_jump_three"] > 0.0
    ):
        return 3
    if d["my_jump_four"] > 0.0:
        return 2
    if (
        d["my_blocked_four"] > 0.0
        or d["my_live_three"] > 0.0
        or d["my_jump_three"] > 0.0
    ):
        return 1
    return 0


def _attack_subscore_from_deltas(d):
    # fine-grained attack score
    return (
        11.0 * max(0.0, d["my_blocked4_and_jump4"])
        + 10.0 * max(0.0, d["my_double_jump_four"])
        + 9.0 * max(0.0, d["my_blocked4_and_live3"])
        + 8.0 * max(0.0, d["my_double_live_three"])
        + 7.0 * max(0.0, d["my_jump3_and_live3"])
        + 6.0 * max(0.0, d["my_double_jump_three"])
        + 5.0 * max(0.0, d["my_jump_four"])
        + 4.0 * max(0.0, d["my_blocked_four"])
        + 3.0 * max(0.0, d["my_live_three"])
        + 2.0 * max(0.0, d["my_jump_three"])
        + 1.0 * max(0.0, d["my_blocked_three"])
    )


def _build_opp_after_cache(board, stone, cand2):
    # cache opponent one-move simulations (board state + extracted features) for reuse
    opp = _other(stone)
    cache = {}

    for m in cand2:
        b = board.copy()
        if not b.place(m, opp):
            continue
        cache[m] = (b, extract_features(b, opp))

    return cache

def _opp_threat_points(opp_after):
    # collect opponent moves that create three-level and four-level threats
    three_pts = set()
    four_pts = set()

    for m, (_, feats) in opp_after.items():
        if (
            feats.get("my_live_four", 0.0) > 0.0
            or feats.get("my_double_blocked_four", 0.0) > 0.0
            or feats.get("my_blocked4_and_jump4", 0.0) > 0.0
            or feats.get("my_double_jump_four", 0.0) > 0.0
            or feats.get("my_blocked4_and_live3", 0.0) > 0.0
        ):
            four_pts.add(m)

        if (
            feats.get("my_double_live_three", 0.0) > 0.0
            or feats.get("my_jump3_and_live3", 0.0) > 0.0
            or feats.get("my_double_jump_three", 0.0) > 0.0
        ):
            three_pts.add(m)

    return three_pts, four_pts


def _opp_next_three_to_threat_points(stone, opp_after):
    # classify opponent one-step simulations into three-threat and four-threat points
    opp = _other(stone)
    pts = set()

    for m1, (b1, feats1) in opp_after.items():
        if (
            feats1.get("my_live_three", 0.0) <= 0.0
            and feats1.get("my_jump_three", 0.0) <= 0.0
        ):
            continue

        for m2 in b1.candidate_moves(radius=2):
            b2 = b1.copy()
            if not b2.place(m2, opp):
                continue

            feats2 = extract_features(b2, opp)
            if (
                feats2.get("my_live_four", 0.0) > 0.0
                or feats2.get("my_blocked4_and_jump4", 0.0) > 0.0
                or feats2.get("my_double_jump_four", 0.0) > 0.0
                or feats2.get("my_blocked4_and_live3", 0.0) > 0.0
                or feats2.get("my_double_live_three", 0.0) > 0.0
                or feats2.get("my_jump3_and_live3", 0.0) > 0.0
                or feats2.get("my_double_jump_three", 0.0) > 0.0
            ):
                pts.add(m1)
                break

    return pts


def _score_sort_key(item):
    # attack-first ordering
    move = item["move"]
    return (
        -item["tier"],
        -int(item["tier"] == 0 and item["covers_three_threat_point"]),
        -int(item["tier"] == 0 and item["blocks_three_to_threat"]),
        -item["subscore"],
        -item["delta"],
        item["dist"],
        move[0],
        move[1],
    )


def _defense_sort_key(item):
    # defense ordering: critical cover first, then threat reduction
    move = item["move"]
    return (
        -item["threat_drop"],
        -item["tier"],
        -item["subscore"],
        -item["delta"],
        item["dist"],
        move[0],
        move[1],
    )


def order_moves(board, moves, stone, weights=None):
    # ordering: # win > block > (defense if required) > attack
    # attack: tier -> cover/block three threats -> subscore -> eval delta -> center
    # defense: cover four threats -> threat drop -> attack value
    # defense mode triggers when no attack and opponent has threats
    if not moves:
        return []

    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    opp = _other(stone)
    center = (board.size // 2, board.size // 2)

    before_eval = evaluate(board, stone, weights=w)
    before_feats = extract_features(board, stone)

    opp_level = _level_from_feats(before_feats, "opp")
    my_level = _level_from_feats(before_feats, "my")

    cand2 = list(board.candidate_moves(radius=2))
    opp_after = _build_opp_after_cache(board, stone, cand2)
    opp_three_threat_points, opp_four_threat_points = _opp_threat_points(opp_after)
    opp_three_to_threat_points = _opp_next_three_to_threat_points(stone, opp_after)

    # defend only if we have no real attack and opponent has pressure
    must_defend = (
        my_level < 1 
        and (opp_level >= 1 or bool(opp_four_threat_points))
    )

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

        after_feats = extract_features(next_board, stone)
        after_eval = evaluate(next_board, stone, weights=w)

        d = _feature_deltas(before_feats, after_feats)
        r, c = move

        scored_moves.append(
            {
                "move": move,
                "next_board": next_board,
                "after_feats": after_feats,
                "tier": _attack_tier_from_deltas(d),
                "subscore": _attack_subscore_from_deltas(d),
                "delta": after_eval - before_eval,
                "dist": abs(r - center[0]) + abs(c - center[1]),
                "covers_four_threat_point": move in opp_four_threat_points,
                "covers_three_threat_point": move in opp_three_threat_points,
                "blocks_three_to_threat": move in opp_three_to_threat_points,
            }
        )

    scored_moves.sort(key=_score_sort_key)

    if not must_defend:
        return winning_moves + blocking_moves + [x["move"] for x in scored_moves]

    before_opp_level = _level_from_feats(before_feats, "opp")
    forced_defense_moves = []

    for item in scored_moves:
        after_opp_level = _level_from_feats(extract_features(item["next_board"], opp), "my")
        threat_drop = before_opp_level - after_opp_level

        # keep only moves that actually reduce opponent threat level
        if item["covers_four_threat_point"] or threat_drop > 0:
            forced_defense_moves.append(
                {
                    "move": item["move"],
                    "threat_drop": threat_drop,
                    "covers_four_threat_point": item["covers_four_threat_point"],
                    "covers_three_threat_point": item["covers_three_threat_point"],
                    "tier": item["tier"],
                    "subscore": item["subscore"],
                    "delta": item["delta"],
                    "dist": item["dist"],
                }
            )

    forced_defense_moves.sort(key=_defense_sort_key)

    if not forced_defense_moves:
        return winning_moves + blocking_moves + [x["move"] for x in scored_moves]

    forced_set = {x["move"] for x in forced_defense_moves}
    remaining = [x["move"] for x in scored_moves if x["move"] not in forced_set]

    return (
        winning_moves
        + blocking_moves
        + [x["move"] for x in forced_defense_moves]
        + remaining
    )


def load_weights_json(path):
    # load weights from json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights_json(path, weights):
    # save weights to json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)