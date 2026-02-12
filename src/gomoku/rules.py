from gomoku.board import BLACK, WHITE, EMPTY, WIN_LENGTH


def winner(grid):
    # Return BLACK or WHITE if a winning sequence exists
    target_white = WHITE * WIN_LENGTH
    target_black = BLACK * WIN_LENGTH
    n = len(grid)

    def check_line(line):
        # Check if a line contains a winning sequence
        s = "".join(line)
        if target_white in s:
            return WHITE
        if target_black in s:
            return BLACK
        return None

    # Check rows
    for row in grid:
        w = check_line(row)
        if w:
            return w

    # Check columns
    for col in zip(*grid):
        w = check_line(col)
        if w:
            return w

    # Check '/' diagonals
    diags = [[] for _ in range(2 * n - 1)]
    for r in range(n):
        for c in range(n):
            diags[r + c].append(grid[r][c])
    for d in diags:
        w = check_line(d)
        if w:
            return w

    # Check '\' diagonals
    diags = [[] for _ in range(2 * n - 1)]
    offset = n - 1
    for r in range(n):
        for c in range(n):
            diags[r - c + offset].append(grid[r][c])
    for d in diags:
        w = check_line(d)
        if w:
            return w

    return None


def is_draw(grid):
    # Return True if board is full and no winner exists
    for row in grid:
        if EMPTY in row:
            return False
    return winner(grid) is None


def is_terminal(grid):
    # Return True if game is over (win or draw)
    return winner(grid) is not None or is_draw(grid)
