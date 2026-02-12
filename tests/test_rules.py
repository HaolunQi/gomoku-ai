from gomoku.board import Board, BLACK, WHITE
from gomoku import rules


def test_winner_none_on_empty_board():
    # Empty board should have no winner, not be terminal, and not be a draw
    b = Board()
    assert rules.winner(b.grid) is None
    assert rules.is_terminal(b.grid) is False
    assert rules.is_draw(b.grid) is False


def test_horizontal_win_black():
    # Five in a row horizontally should win
    b = Board()
    row = 7
    for col in range(5):
        assert b.place((row, col), BLACK)
    assert rules.winner(b.grid) == BLACK
    assert rules.is_terminal(b.grid) is True


def test_vertical_win_white():
    # Five in a row vertically should win
    b = Board()
    col = 3
    for row in range(5):
        assert b.place((row, col), WHITE)
    assert rules.winner(b.grid) == WHITE


def test_diagonal_backslash_win_black():
    # '\\' diagonal should be detected as a win
    b = Board()
    for i in range(5):
        assert b.place((i, i), BLACK)
    assert rules.winner(b.grid) == BLACK


def test_diagonal_slash_win_white():
    # '/' diagonal should be detected as a win
    b = Board()
    for i in range(5):
        assert b.place((i, 4 - i), WHITE)
    assert rules.winner(b.grid) == WHITE


def test_no_false_positive_with_gaps():
    # Non-consecutive stones should not be treated as a win
    b = Board()
    row = 10
    for col in range(4):
        assert b.place((row, col), BLACK)
    assert b.place((row, 5), BLACK)
    assert rules.winner(b.grid) is None


def test_draw_on_full_small_grid_without_winner():
    # A full board smaller than WIN_LENGTH should be a draw
    grid = [
        [BLACK, WHITE, BLACK, WHITE],
        [WHITE, BLACK, WHITE, BLACK],
        [BLACK, WHITE, BLACK, WHITE],
        [WHITE, BLACK, WHITE, BLACK],
    ]
    assert rules.winner(grid) is None
    assert rules.is_draw(grid) is True
    assert rules.is_terminal(grid) is True


def test_is_terminal_true_when_winner():
    # Terminal should be True if a winner exists
    b = Board()
    for i in range(5):
        assert b.place((0, i), BLACK)
    assert rules.is_terminal(b.grid) is True
    assert rules.is_draw(b.grid) is False
