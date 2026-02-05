from __future__ import annotations
from typing import Tuple, Sequence
from .board import BLACK, WHITE, EMPTY, WIN_LENGTH, Stone

Grid = Sequence[Sequence[str]] # Grid: rows × cols
Line = Tuple[str, ...] # One line (row / col / diagonal)
Lines = Tuple[Line, ...] # Collection of lines


def _winner_in_lines(lines: Lines) -> Stone | None:
    """Return WHITE or BLACK if any line contains WIN_LENGTH consecutive stones; else None."""
    target_white = WHITE * WIN_LENGTH
    target_black = BLACK * WIN_LENGTH

    for line in lines:
        s = "".join(line)
        if target_white in s:
            return WHITE
        if target_black in s:
            return BLACK
    return None


def _rows(grid: Grid) -> Lines:
    """All horizontal lines (each row)."""
    return tuple(tuple(row) for row in grid)


def _cols(grid: Grid) -> Lines:
    """All vertical lines (each column)."""
    return tuple(tuple(col) for col in zip(*grid))


def _diagonals_slash(grid: Grid) -> Lines:
    """
    Diagonals in the '/' direction.
    Cells share the same (x + y). Range: 0 .. 2n-2.
    """
    n = len(grid)
    diags = [[] for _ in range(2 * n - 1)]
    for row in range(n):
        for col in range(n):
            diags[row + col].append(grid[row][col])
    return tuple(tuple(d) for d in diags)


def _diagonals_backslash(grid: Grid) -> Lines:
    """
    Diagonals in the '\\' direction.
    Cells share the same (x - y). Range: -(n-1) .. (n-1), shifted by + (n-1).
    """
    n = len(grid)
    offset = n - 1
    diags = [[] for _ in range(2 * n - 1)]
    for row in range(n):
        for col in range(n):
            diags[row - col + offset].append(grid[row][col])
    return tuple(tuple(d) for d in diags)


def winner(grid: Grid) -> Stone | None:
    """
    Check the 4 directions (rows, cols, / diagonals, \\ diagonals).
    Return WHITE/BLACK if found; otherwise None.
    """
    lines = (
        _rows(grid)
        + _cols(grid)
        + _diagonals_slash(grid)
        + _diagonals_backslash(grid)
    )
    return _winner_in_lines(lines)


def is_draw(grid: Grid) -> bool:
    """Return True iff the board is full and there is no winner."""
    for row in grid:
        if EMPTY in row:
            return False
    return winner(grid) is None


def is_terminal(grid: Grid) -> bool:
    """Game is terminal iff there is a winner or a draw."""
    return winner(grid) is not None or is_draw(grid)
