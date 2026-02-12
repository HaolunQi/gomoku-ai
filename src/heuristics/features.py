# heuristics/features.py
# Shared feature extraction used by AB + RL
# IMPORTANT: Keep features simple + stable. Add new features only when tests cover them.

from gomoku.board import BLACK, WHITE, EMPTY

# TODO: decide a canonical feature set with teammate B:
#   - center_distance
#   - immediate_win_threats
#   - open_threes / open_fours counts (later)
#   - stone_count, mobility, etc.
# Keep it minimal at first.


def extract_features(board, stone):
    # Return a dict[str, float]-like mapping (plain dict is fine)
    # TODO: implement real features; for now provide a tiny stable set.
    opp = WHITE if stone == BLACK else BLACK
    grid = board.grid
    n = board.size

    my_count = 0
    opp_count = 0
    empty_count = 0

    for r in range(n):
        row = grid[r]
        for c in range(n):
            v = row[c]
            if v == stone:
                my_count += 1
            elif v == opp:
                opp_count += 1
            elif v == EMPTY:
                empty_count += 1

    # A trivial feature that is always defined
    feats = {
        "my_stones": float(my_count),
        "opp_stones": float(opp_count),
        "empty": float(empty_count),
    }

    # TODO: add center bias feature
    # TODO: add pattern-based features for gomoku shapes (live two, live three, etc.)
    # TODO: add "last_move proximity" feature

    return feats


def featurize_after_move(board, stone, move):
    # Convenience for RL: copy board, apply move, then extract features
    # TODO: consider optimizing to avoid full copy (later)
    b2 = board.copy()
    ok = b2.place(move, stone)
    if not ok:
        # Keep safe: return base features
        return extract_features(board, stone)
    return extract_features(b2, stone)
