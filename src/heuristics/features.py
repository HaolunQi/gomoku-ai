from gomoku.board import BLACK, WHITE, EMPTY


def _other(stone):
    # return opponent stone
    return WHITE if stone == BLACK else BLACK


def _iter_lines(grid):
    # iterate all rows, columns, and diagonals
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
    # count patterns in a single line
    n = len(line)

    live_two = 0
    blocked_two = 0
    live_three = 0
    blocked_three = 0
    live_four = 0
    blocked_four = 0
    jump_two = 0
    blocked_jump_two = 0
    jump_three = 0
    blocked_jump_three = 0
    jump_four = 0
    blocked_jump_four = 0

    i = 0
    while i < n:
        if line[i] != stone:
            i += 1
            continue

        j = i
        while j < n and line[j] == stone:
            j += 1

        run_len = j - i

        # check openness of ends
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
    
    # open jump two patterns
    open_jump_two_patterns = [
        [EMPTY, stone, EMPTY, stone, EMPTY],
    ]

    # blocked jump two patterns
    blocked_jump_two_patterns = [
        [stone, EMPTY, stone, EMPTY],
        [EMPTY, stone, EMPTY, stone],
    ]

    # open jump two
    for i in range(n - 4):
        if line[i:i + 5] in open_jump_two_patterns:
            jump_two += 1

    # blocked jump two
    for i in range(n - 3):
        if line[i:i + 4] in blocked_jump_two_patterns:
            blocked_jump_two += 1

    # open jump three patterns
    open_jump_three_patterns = [
        [EMPTY, stone, stone, EMPTY, stone, EMPTY],
        [EMPTY, stone, EMPTY, stone, stone, EMPTY],
    ]

    for i in range(n - 5):
        if line[i:i + 6] in open_jump_three_patterns:
            jump_three += 1

    # blocked jump three patterns
    blocked_jump_three_patterns = [
        [stone, stone, EMPTY, stone, EMPTY],
        [stone, EMPTY, stone, stone, EMPTY],
        [EMPTY, stone, stone, EMPTY, stone],
        [EMPTY, stone, EMPTY, stone, stone],
    ]

    for i in range(n - 4):
        if line[i:i + 5] in blocked_jump_three_patterns:
            blocked_jump_three += 1

    # open jump four patterns
    open_jump_four_patterns = [
        [EMPTY, stone, stone, stone, EMPTY, stone, EMPTY],
        [EMPTY, stone, stone, EMPTY, stone, stone, EMPTY],
        [EMPTY, stone, EMPTY, stone, stone, stone, EMPTY],
    ]

    for i in range(n - 6):
        if line[i:i + 7] in open_jump_four_patterns:
            jump_four += 1

    # blocked jump four patterns
    blocked_jump_four_patterns = [
        [stone, stone, stone, EMPTY, stone, EMPTY],
        [stone, stone, EMPTY, stone, stone, EMPTY],
        [stone, EMPTY, stone, stone, stone, EMPTY],
        [EMPTY, stone, stone, stone, EMPTY, stone],
        [EMPTY, stone, stone, EMPTY, stone, stone],
        [EMPTY, stone, EMPTY, stone, stone, stone],
    ]

    for i in range(n - 5):
        if line[i:i + 6] in blocked_jump_four_patterns:
            blocked_jump_four += 1

    return {
        "live_two": live_two,
        "blocked_two": blocked_two,
        "live_three": live_three,
        "blocked_three": blocked_three,
        "live_four": live_four,
        "blocked_four": blocked_four,
        "jump_two": jump_two,
        "blocked_jump_two": blocked_jump_two,
        "jump_three": jump_three,
        "blocked_jump_three": blocked_jump_three,
        "jump_four": jump_four,
        "blocked_jump_four": blocked_jump_four,
    }


def _collect_patterns(grid, stone):
    # aggregate pattern counts over all lines
    totals = {
        "live_two": 0,
        "blocked_two": 0,
        "live_three": 0,
        "blocked_three": 0,
        "live_four": 0,
        "blocked_four": 0,
        "jump_two": 0,
        "blocked_jump_two": 0,
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
    # extract global features for both sides
    opp = _other(stone)
    grid = board.grid
    n = board.size

    my_count = 0
    opp_count = 0
    empty_count = 0

    for r in range(n):
        for c in range(n):
            v = grid[r][c]
            if v == stone:
                my_count += 1
            elif v == opp:
                opp_count += 1
            elif v == EMPTY:
                empty_count += 1

    my_patterns = _collect_patterns(grid, stone)
    opp_patterns = _collect_patterns(grid, opp)

    # derived combo features
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
    opp_blocked4_and_jump3 = 1.0 if opp_patterns["blocked_four"] >= 1 and opp_patterns["jump_three"] >= 1 else 0.0

    my_double_jump_four = 1.0 if my_patterns["jump_four"] >= 2 else 0.0
    opp_double_jump_four = 1.0 if opp_patterns["jump_four"] >= 2 else 0.0

    my_jump4_and_live3 = 1.0 if my_patterns["jump_four"] >= 1 and my_patterns["live_three"] >= 1 else 0.0
    opp_jump4_and_live3 = 1.0 if opp_patterns["jump_four"] >= 1 and opp_patterns["live_three"] >= 1 else 0.0

    my_jump4_and_jump3 = 1.0 if my_patterns["jump_four"] >= 1 and my_patterns["jump_three"] >= 1 else 0.0
    opp_jump4_and_jump3 = 1.0 if opp_patterns["jump_four"] >= 1 and opp_patterns["jump_three"] >= 1 else 0.0

    feats = {
        # counts
        "my_stones": float(my_count),
        "opp_stones": float(opp_count),
        "empty": float(empty_count),

        # my patterns
        "my_live_two": float(my_patterns["live_two"]),
        "my_blocked_two": float(my_patterns["blocked_two"]),
        "my_live_three": float(my_patterns["live_three"]),
        "my_blocked_three": float(my_patterns["blocked_three"]),
        "my_live_four": float(my_patterns["live_four"]),
        "my_blocked_four": float(my_patterns["blocked_four"]),
        "my_jump_two": float(my_patterns["jump_two"]),
        "my_blocked_jump_two": float(my_patterns["blocked_jump_two"]),
        "my_jump_three": float(my_patterns["jump_three"]),
        "my_blocked_jump_three": float(my_patterns["blocked_jump_three"]),
        "my_jump_four": float(my_patterns["jump_four"]),
        "my_blocked_jump_four": float(my_patterns["blocked_jump_four"]),

        # opponent patterns
        "opp_live_two": float(opp_patterns["live_two"]),
        "opp_blocked_two": float(opp_patterns["blocked_two"]),
        "opp_live_three": float(opp_patterns["live_three"]),
        "opp_blocked_three": float(opp_patterns["blocked_three"]),
        "opp_live_four": float(opp_patterns["live_four"]),
        "opp_blocked_four": float(opp_patterns["blocked_four"]),
        "opp_jump_two": float(opp_patterns["jump_two"]),
        "opp_blocked_jump_two": float(opp_patterns["blocked_jump_two"]),
        "opp_jump_three": float(opp_patterns["jump_three"]),
        "opp_blocked_jump_three": float(opp_patterns["blocked_jump_three"]),
        "opp_jump_four": float(opp_patterns["jump_four"]),
        "opp_blocked_jump_four": float(opp_patterns["blocked_jump_four"]),

        # combo features
        "my_double_live_three": my_double_live_three,
        "my_double_jump_three": my_double_jump_three,
        "my_jump3_and_live3": my_jump3_and_live3,
        "my_double_blocked_four": my_double_blocked_four,
        "my_blocked4_and_jump4": my_blocked4_and_jump4,
        "my_blocked4_and_live3": my_blocked4_and_live3,
        "my_blocked4_and_jump3": my_blocked4_and_jump3,
        "my_double_jump_four": my_double_jump_four,
        "my_jump4_and_live3": my_jump4_and_live3,
        "my_jump4_and_jump3": my_jump4_and_jump3,

        "opp_double_live_three": opp_double_live_three,
        "opp_double_jump_three": opp_double_jump_three,
        "opp_jump3_and_live3": opp_jump3_and_live3,
        "opp_double_blocked_four": opp_double_blocked_four,
        "opp_blocked4_and_jump4": opp_blocked4_and_jump4,
        "opp_blocked4_and_live3": opp_blocked4_and_live3,
        "opp_blocked4_and_jump3": opp_blocked4_and_jump3,
        "opp_double_jump_four": opp_double_jump_four,
        "opp_jump4_and_live3": opp_jump4_and_live3,
        "opp_jump4_and_jump3": opp_jump4_and_jump3,
    }

    return feats


def featurize_after_move(board, stone, move):
    # features after applying move
    b2 = board.copy()
    ok = b2.place(move, stone)
    if not ok:
        return extract_features(board, stone)
    return extract_features(b2, stone)