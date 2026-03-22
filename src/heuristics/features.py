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


def _other(stone):
    return WHITE if stone == BLACK else BLACK


def _iter_lines(grid):
    # Iterate all rows, columns, and diagonals
    n = len(grid)

    # rows
    for r in range(n):
        yield list(grid[r])

    # columns
    for c in range(n):
        yield [grid[r][c] for r in range(n)]

    # "\" diagonals
    for d in range(-n + 1, n):
        line = []
        for r in range(n):
            c = r - d
            if 0 <= c < n:
                line.append(grid[r][c])
        if len(line) >= 2:
            yield line

    # "/" diagonals
    for d in range(2 * n - 1):
        line = []
        for r in range(n):
            c = d - r
            if 0 <= c < n:
                line.append(grid[r][c])
        if len(line) >= 2:
            yield line


def _count_line_patterns(line, stone):
    # Count patterns in a single line:
    # live two / blocked two / live three / blocked three / live four / blocked four

    n = len(line)

    live_two = 0
    blocked_two = 0
    live_three = 0
    blocked_three = 0
    live_four = 0
    blocked_four = 0

    i = 0
    while i < n:
        if line[i] != stone:
            i += 1
            continue

        j = i
        while j < n and line[j] == stone:
            j += 1

        run_len = j - i

        # Treat boundary as blocked
        left_open = (i - 1 >= 0 and line[i - 1] == EMPTY)
        right_open = (j < n and line[j] == EMPTY)

        if run_len == 2:
            if left_open and right_open:
                live_two += 1
            elif left_open or right_open:
                blocked_two += 1

        elif run_len == 3:
            if left_open and right_open:
                live_three += 1
            elif left_open or right_open:
                blocked_three += 1

        elif run_len == 4:
            if left_open and right_open:
                live_four += 1
            elif left_open or right_open:
                blocked_four += 1

        i = j

    return {
        "live_two": live_two,
        "blocked_two": blocked_two,
        "live_three": live_three,
        "blocked_three": blocked_three,
        "live_four": live_four,
        "blocked_four": blocked_four,
    }


def _collect_patterns(grid, stone):
    # Aggregate pattern counts over all lines
    totals = {
        "live_two": 0,
        "blocked_two": 0,
        "live_three": 0,
        "blocked_three": 0,
        "live_four": 0,
        "blocked_four": 0,
    }

    for line in _iter_lines(grid):
        counts = _count_line_patterns(line, stone)
        for k in totals:
            totals[k] += counts[k]

    return totals


def extract_features(board, stone):
    # Return a dict[str, float]-like mapping (plain dict is fine)
    # TODO: implement real features; for now provide a tiny stable set.

    opp = _other(stone)
    grid = board.grid
    n = board.size

    # --- basic counts ---
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

    # --- pattern features ---
    my_patterns = _collect_patterns(grid, stone)
    opp_patterns = _collect_patterns(grid, opp)

    # --- combined patterns ---
    my_double_live_three = 1.0 if my_patterns["live_three"] >= 2 else 0.0
    opp_double_live_three = 1.0 if opp_patterns["live_three"] >= 2 else 0.0

    my_double_blocked_four = 1.0 if my_patterns["blocked_four"] >= 2 else 0.0
    opp_double_blocked_four = 1.0 if opp_patterns["blocked_four"] >= 2 else 0.0

    my_four_and_live_three = 1.0 if (
        my_patterns["blocked_four"] >= 1 and my_patterns["live_three"] >= 1
    ) else 0.0

    opp_four_and_live_three = 1.0 if (
        opp_patterns["blocked_four"] >= 1 and opp_patterns["live_three"] >= 1
    ) else 0.0

    # A stable feature dictionary
    feats = {
        "my_stones": float(my_count),
        "opp_stones": float(opp_count),
        "empty": float(empty_count),

        "my_live_two": float(my_patterns["live_two"]),
        "my_blocked_two": float(my_patterns["blocked_two"]),
        "my_live_three": float(my_patterns["live_three"]),
        "my_blocked_three": float(my_patterns["blocked_three"]),
        "my_live_four": float(my_patterns["live_four"]),
        "my_blocked_four": float(my_patterns["blocked_four"]),

        "opp_live_two": float(opp_patterns["live_two"]),
        "opp_blocked_two": float(opp_patterns["blocked_two"]),
        "opp_live_three": float(opp_patterns["live_three"]),
        "opp_blocked_three": float(opp_patterns["blocked_three"]),
        "opp_live_four": float(opp_patterns["live_four"]),
        "opp_blocked_four": float(opp_patterns["blocked_four"]),

        "my_double_live_three": my_double_live_three,
        "opp_double_live_three": opp_double_live_three,

        "my_double_blocked_four": my_double_blocked_four,
        "opp_double_blocked_four": opp_double_blocked_four,

        "my_four_and_live_three": my_four_and_live_three,
        "opp_four_and_live_three": opp_four_and_live_three,
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