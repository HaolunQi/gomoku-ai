# heuristics/features.py
# Shared feature extraction used by AB + RL

from gomoku.board import BLACK, WHITE, EMPTY

# Directions: horizontal, vertical, two diagonals
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


def _count_patterns(grid, n, stone):
    """Count gomoku line patterns for the given stone.

    Scans every line (row, col, diag) and counts:
      - open_four:  4 in a row with both ends open  (winning threat)
      - half_four:  4 in a row with one end open     (must block)
      - open_three: 3 in a row with both ends open   (strong threat)
      - half_three: 3 in a row with one end open
      - open_two:   2 in a row with both ends open
    """
    opp = WHITE if stone == BLACK else BLACK
    counts = {
        "open_four": 0,
        "half_four": 0,
        "open_three": 0,
        "half_three": 0,
        "open_two": 0,
    }

    visited = set()

    for r in range(n):
        for c in range(n):
            if grid[r][c] != stone:
                continue
            for dr, dc in DIRECTIONS:
                # Only count each line once (start from the first stone in the line)
                pr, pc = r - dr, c - dc
                if 0 <= pr < n and 0 <= pc < n and grid[pr][pc] == stone:
                    continue

                # Count consecutive stones in this direction
                length = 0
                cr, cc = r, c
                while 0 <= cr < n and 0 <= cc < n and grid[cr][cc] == stone:
                    length += 1
                    cr += dr
                    cc += dc

                if length < 2 or length >= 5:
                    continue

                # Check ends: before the line start and after the line end
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


def extract_features(board, stone):
    """Return a dict of features for the given board state and stone color."""
    opp = WHITE if stone == BLACK else BLACK
    grid = board.grid
    n = board.size

    my_patterns = _count_patterns(grid, n, stone)
    opp_patterns = _count_patterns(grid, n, opp)

    # Normalize pattern counts to [0, 1] range by dividing by reasonable max.
    # On a 9x9 board you rarely see more than ~4 of any pattern at once.
    PAT_NORM = 4.0

    feats = {
        "bias": 1.0,
        "my_open_four": float(my_patterns["open_four"]) / PAT_NORM,
        "my_half_four": float(my_patterns["half_four"]) / PAT_NORM,
        "my_open_three": float(my_patterns["open_three"]) / PAT_NORM,
        "my_half_three": float(my_patterns["half_three"]) / PAT_NORM,
        "my_open_two": float(my_patterns["open_two"]) / PAT_NORM,
        # Opponent features are negative: having opponent threats is BAD
        "opp_open_four": -float(opp_patterns["open_four"]) / PAT_NORM,
        "opp_half_four": -float(opp_patterns["half_four"]) / PAT_NORM,
        "opp_open_three": -float(opp_patterns["open_three"]) / PAT_NORM,
        "opp_half_three": -float(opp_patterns["half_three"]) / PAT_NORM,
        "opp_open_two": -float(opp_patterns["open_two"]) / PAT_NORM,
    }

    # Center control: average distance of my stones from center, normalized
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


def featurize_after_move(board, stone, move):
    """For RL: copy board, apply move, then extract features."""
    b2 = board.copy()
    ok = b2.place(move, stone)
    if not ok:
        return extract_features(board, stone)
    return extract_features(b2, stone)
