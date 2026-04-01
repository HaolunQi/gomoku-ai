# heuristics/features.py
# Shared feature extraction used by AB + RL

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
    blocked_jump_three = 0
    jump_four = 0
    blocked_jump_four = 0

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

    # --- jump-three / blocked-jump-three ---
    for i in range(n - 4):
        w = line[i:i + 5]

        patterns = [
            [EMPTY, stone, stone, EMPTY, stone],
            [EMPTY, stone, EMPTY, stone, stone],
            [stone, stone, EMPTY, stone, EMPTY],
            [stone, EMPTY, stone, stone, EMPTY],
        ]

        if w in patterns:
            left_open = (i - 1 >= 0 and line[i - 1] == EMPTY)
            right_open = (i + 5 < n and line[i + 5] == EMPTY)

            if left_open and right_open:
                jump_three += 1
            else:
                blocked_jump_three += 1

    # --- jump-four / blocked-jump-four ---
    for i in range(n - 4):
        w = line[i:i + 5]

        patterns = [
            [stone, stone, stone, EMPTY, stone],
            [stone, stone, EMPTY, stone, stone],
            [stone, EMPTY, stone, stone, stone],
        ]

        if w in patterns:
            left_open = (i - 1 >= 0 and line[i - 1] == EMPTY)
            right_open = (i + 5 < n and line[i + 5] == EMPTY)

            if left_open and right_open:
                jump_four += 1
            else:
                blocked_jump_four += 1

    return {
        "live_two": live_two,
        "blocked_two": blocked_two,
        "live_three": live_three,
        "blocked_three": blocked_three,
        "live_four": live_four,
        "blocked_four": blocked_four,
        "jump_three": jump_three,
        "blocked_jump_three": blocked_jump_three,
        "jump_four": jump_four,
        "blocked_jump_four": blocked_jump_four,
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
        "blocked_jump_three": 0,
        "jump_four": 0,
        "blocked_jump_four": 0,
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

    # Normalize pattern counts to [0, 1] range by dividing by reasonable max.
    # On a 9x9 board you rarely see more than ~4 of any pattern at once.
    PAT_NORM = 4.0

    # --- pattern features ---
    my_patterns = _collect_patterns(grid, stone)
    opp_patterns = _collect_patterns(grid, opp)

    # --- combined patterns ---
    # Keep our own attacking combos conservative:
    # do NOT let jump-three strongly boost our own offense.
    # But do treat opponent jump-three as a real danger signal.

    my_double_live_three = 1.0 if my_patterns["live_three"] >= 2 else 0.0
    opp_double_live_three = 1.0 if opp_patterns["live_three"] >= 2 else 0.0

    my_double_jump_three = 1.0 if my_patterns["jump_three"] >= 2 else 0.0
    opp_double_jump_three = 1.0 if opp_patterns["jump_three"] >= 2 else 0.0

    my_jump3_and_live3 = 1.0 if my_patterns["jump_three"] >= 1 and my_patterns["live_three"] >= 1 else 0.0
    opp_jump3_and_live3 = 1.0 if opp_patterns["jump_three"] >= 1 and opp_patterns["live_three"] >= 1 else 0.0

    my_double_blocked_four = 1.0 if my_patterns["blocked_four"] >= 2 else 0.0
    opp_double_blocked_four = 1.0 if opp_patterns["blocked_four"] >= 2 else 0.0

    my_blocked4_and_jump4 = 1.0 if my_patterns["blocked_four"] >= 1 and my_patterns["jump_four"] >= 1 else 0.0
    opp_blocked4_and_jump4 = 1.0 if opp_patterns["blocked_four"] >= 1 and opp_patterns["jump_four"] >= 1 else 0.0

    my_blocked4_and_live3 = 1.0 if my_patterns["blocked_four"] >= 1 and my_patterns["live_three"] >= 1 else 0.0
    opp_blocked4_and_live3 = 1.0 if opp_patterns["blocked_four"] >= 1 and opp_patterns["live_three"] >= 1 else 0.0

    my_blocked4_and_jump3 = 1.0 if my_patterns["blocked_four"] >= 1 and my_patterns["jump_three"] >= 1 else 0.0
    oop_blocked4_and_jump3 = 1.0 if opp_patterns["blocked_four"] >= 1 and opp_patterns["jump_three"] >= 1 else 0.0

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
        "my_blocked_jump_three": float(my_patterns["blocked_jump_three"]),
        "my_jump_four": float(my_patterns["jump_four"]),
        "my_blocked_jump_four": float(my_patterns["blocked_jump_four"]),

        "opp_live_two": float(opp_patterns["live_two"]),
        "opp_blocked_two": float(opp_patterns["blocked_two"]),
        "opp_live_three": float(opp_patterns["live_three"]),
        "opp_blocked_three": float(opp_patterns["blocked_three"]),
        "opp_live_four": float(opp_patterns["live_four"]),
        "opp_blocked_four": float(opp_patterns["blocked_four"]),
        "opp_jump_three": float(opp_patterns["jump_three"]),
        "opp_blocked_jump_three": float(opp_patterns["blocked_jump_three"]),
        "opp_jump_four": float(opp_patterns["jump_four"]),
        "opp_blocked_jump_four": float(opp_patterns["blocked_jump_four"]),

        "my_double_live_three": my_double_live_three,
        "my_double_jump_three": my_double_jump_three,
        "my_jump3_and_live3": my_jump3_and_live3,
        "my_double_blocked_four": my_double_blocked_four,
        "my_blocked4_and_jump4": my_blocked4_and_jump4,
        "my_blocked4_and_live3": my_blocked4_and_live3,
        "my_blocked4_and_jump3": my_blocked4_and_jump3,

        "opp_double_live_three": opp_double_live_three,
        "opp_double_jump_three": opp_double_jump_three,
        "opp_jump3_and_live3": opp_jump3_and_live3,
        "opp_double_blocked_four": opp_double_blocked_four,
        "opp_blocked4_and_jump4": opp_blocked4_and_jump4,
        "opp_blocked4_and_live3": opp_blocked4_and_live3,
        "oop_blocked4_and_jump3": oop_blocked4_and_jump3,
    }

    return feats


<<<<<<< HEAD
=======
# --- RL Q-learning feature set (keys must match weights_rl.json) ----------------

DIRECTIONS_RL = [(0, 1), (1, 0), (1, 1), (1, -1)]


def _count_rl_patterns(grid, n, stone):
    """Count open_two / half_three / open_three / half_four / open_four line patterns."""
    counts = {
        "open_four": 0,
        "half_four": 0,
        "open_three": 0,
        "half_three": 0,
        "open_two": 0,
    }

    for r in range(n):
        for c in range(n):
            if grid[r][c] != stone:
                continue
            for dr, dc in DIRECTIONS_RL:
                pr, pc = r - dr, c - dc
                if 0 <= pr < n and 0 <= pc < n and grid[pr][pc] == stone:
                    continue

                length = 0
                cr, cc = r, c
                while 0 <= cr < n and 0 <= cc < n and grid[cr][cc] == stone:
                    length += 1
                    cr += dr
                    cc += dc

                if length < 2 or length >= 5:
                    continue

                br, bc = r - dr, c - dc
                before_open = (0 <= br < n and 0 <= bc < n and grid[br][bc] == EMPTY)
                after_open = (0 <= cr < n and 0 <= cc < n and grid[cr][cc] == EMPTY)

                open_ends = int(before_open) + int(after_open)

                if length == 4:
                    if open_ends == 2:
                        counts["open_four"] += 1
                    elif open_ends == 1:
                        counts["half_four"] += 1
                elif length == 3:
                    if open_ends == 2:
                        counts["open_three"] += 1
                    elif open_ends == 1:
                        counts["half_three"] += 1
                elif length == 2:
                    if open_ends == 2:
                        counts["open_two"] += 1

    return counts


def extract_rl_features(board, stone):
    """19-feature vector for linear Q-learning.

    13 original features + 6 interaction features for double-threat combos.
    """
    opp = WHITE if stone == BLACK else BLACK
    grid = board.grid
    n = board.size

    my_patterns = _count_rl_patterns(grid, n, stone)
    opp_patterns = _count_rl_patterns(grid, n, opp)

    PAT_NORM = 4.0

    feats = {
        "bias": 1.0,
        "my_open_four": float(my_patterns["open_four"]) / PAT_NORM,
        "my_half_four": float(my_patterns["half_four"]) / PAT_NORM,
        "my_open_three": float(my_patterns["open_three"]) / PAT_NORM,
        "my_half_three": float(my_patterns["half_three"]) / PAT_NORM,
        "my_open_two": float(my_patterns["open_two"]) / PAT_NORM,
        "opp_open_four": -float(opp_patterns["open_four"]) / PAT_NORM,
        "opp_half_four": -float(opp_patterns["half_four"]) / PAT_NORM,
        "opp_open_three": -float(opp_patterns["open_three"]) / PAT_NORM,
        "opp_half_three": -float(opp_patterns["half_three"]) / PAT_NORM,
        "opp_open_two": -float(opp_patterns["open_two"]) / PAT_NORM,
    }

    # --- interaction features: double-threat combos ---
    # These capture "two threats at once = forced win" which linear models
    # can't learn from individual features alone.

    # My double threats (basically forced wins)
    feats["my_four_and_three"] = 1.0 if (
        my_patterns["half_four"] >= 1 and my_patterns["open_three"] >= 1
    ) else 0.0

    feats["my_double_three"] = 1.0 if (
        my_patterns["open_three"] >= 2
    ) else 0.0

    feats["my_double_four"] = 1.0 if (
        my_patterns["half_four"] >= 2
    ) else 0.0

    # Opponent double threats (urgent danger — block or lose)
    feats["opp_four_and_three"] = -1.0 if (
        opp_patterns["half_four"] >= 1 and opp_patterns["open_three"] >= 1
    ) else 0.0

    feats["opp_double_three"] = -1.0 if (
        opp_patterns["open_three"] >= 2
    ) else 0.0

    feats["opp_double_four"] = -1.0 if (
        opp_patterns["half_four"] >= 2
    ) else 0.0

    center = n / 2.0
    my_count = 0
    my_center_dist = 0.0
    for r in range(n):
        for c in range(n):
            if grid[r][c] == stone:
                my_count += 1
                my_center_dist += abs(r - center) + abs(c - center)

    total_cells = float(n * n)
    feats["my_stones"] = float(my_count) / total_cells
    feats["center_control"] = float(my_center_dist / max(my_count, 1)) / n

    return feats


>>>>>>> d396863 (Add interaction features and fix gamma default for RL agent)
def featurize_after_move(board, stone, move):
    # Convenience for RL: copy board, apply move, then extract features
    b2 = board.copy()
    ok = b2.place(move, stone)
    if not ok:
        return extract_features(board, stone)
    return extract_features(b2, stone)