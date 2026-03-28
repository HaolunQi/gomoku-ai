# heuristics/features.py
# Shared feature extraction used by AB + RL
# IMPORTANT: Keep features simple + stable. Add new features only when tests cover them.

from gomoku.board import BLACK, WHITE, EMPTY


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
    # plus jump three / jump four

    n = len(line)

    live_two = 0
    blocked_two = 0
    live_three = 0
    blocked_three = 0
    live_four = 0
    blocked_four = 0
    jump_three = 0
    jump_four = 0

    # --- original consecutive-run logic ---
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

    # --- new: detect jump-three in length-5 windows ---
    # .XX.X
    # .X.XX
    # XX.X.
    # X.XX.
    for i in range(n - 4):
        w = line[i:i + 5]

        if w == [EMPTY, stone, stone, EMPTY, stone]:
            jump_three += 1
        elif w == [EMPTY, stone, EMPTY, stone, stone]:
            jump_three += 1
        elif w == [stone, stone, EMPTY, stone, EMPTY]:
            jump_three += 1
        elif w == [stone, EMPTY, stone, stone, EMPTY]:
            jump_three += 1

    # --- new: detect jump-four in length-5 windows ---
    # XXX.X
    # XX.XX
    # X.XXX
    for i in range(n - 4):
        w = line[i:i + 5]

        if w == [stone, stone, stone, EMPTY, stone]:
            jump_four += 1
        elif w == [stone, stone, EMPTY, stone, stone]:
            jump_four += 1
        elif w == [stone, EMPTY, stone, stone, stone]:
            jump_four += 1

    return {
        "live_two": live_two,
        "blocked_two": blocked_two,
        "live_three": live_three,
        "blocked_three": blocked_three,
        "live_four": live_four,
        "blocked_four": blocked_four,
        "jump_three": jump_three,
        "jump_four": jump_four,
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
        "jump_three": 0,
        "jump_four": 0,
    }

    for line in _iter_lines(grid):
        counts = _count_line_patterns(line, stone)
        for k in totals:
            totals[k] += counts[k]

    return totals


def extract_features(board, stone):
    # Return a dict[str, float]-like mapping (plain dict is fine)

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
    # Keep our own attacking combos conservative:
    # do NOT let jump-three strongly boost our own offense.
    # But do treat opponent jump-three as a real danger signal.

    my_double_live_three = 1.0 if my_patterns["live_three"] >= 2 else 0.0
    opp_double_live_three = 1.0 if (
        opp_patterns["live_three"] + opp_patterns["jump_three"] >= 2
    ) else 0.0

    my_double_blocked_four = 1.0 if my_patterns["blocked_four"] >= 2 else 0.0
    opp_double_blocked_four = 1.0 if opp_patterns["blocked_four"] >= 2 else 0.0

    my_four_and_live_three = 1.0 if (
        my_patterns["blocked_four"] >= 1 and my_patterns["live_three"] >= 1
    ) else 0.0

    opp_four_and_live_three = 1.0 if (
        opp_patterns["blocked_four"] >= 1 and
        (opp_patterns["live_three"] + opp_patterns["jump_three"] >= 1)
    ) else 0.0

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
        "my_jump_three": float(my_patterns["jump_three"]),
        "my_jump_four": float(my_patterns["jump_four"]),

        "opp_live_two": float(opp_patterns["live_two"]),
        "opp_blocked_two": float(opp_patterns["blocked_two"]),
        "opp_live_three": float(opp_patterns["live_three"]),
        "opp_blocked_three": float(opp_patterns["blocked_three"]),
        "opp_live_four": float(opp_patterns["live_four"]),
        "opp_blocked_four": float(opp_patterns["blocked_four"]),
        "opp_jump_three": float(opp_patterns["jump_three"]),
        "opp_jump_four": float(opp_patterns["jump_four"]),

        "my_double_live_three": my_double_live_three,
        "opp_double_live_three": opp_double_live_three,

        "my_double_blocked_four": my_double_blocked_four,
        "opp_double_blocked_four": opp_double_blocked_four,

        "my_four_and_live_three": my_four_and_live_three,
        "opp_four_and_live_three": opp_four_and_live_three,
    }

    return feats


def featurize_after_move(board, stone, move):
    # Convenience for RL: copy board, apply move, then extract features
    b2 = board.copy()
    ok = b2.place(move, stone)
    if not ok:
        return extract_features(board, stone)
    return extract_features(b2, stone)