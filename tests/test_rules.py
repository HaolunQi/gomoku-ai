from gomoku.board import Board, BLACK, WHITE
from gomoku import rules


def test_winner_none_on_empty_board():
    b = Board()
    assert rules.winner(b.grid) is None
    assert rules.is_terminal(b.grid) is False
    assert rules.is_draw(b.grid) is False


def test_horizontal_win_black():
    b = Board()
    row = 7
    for col in range(5):
        assert b.place((row, col), BLACK)
    assert rules.winner(b.grid) == BLACK
    assert rules.is_terminal(b.grid) is True


def test_vertical_win_white():
    b = Board()
    col = 3
    for row in range(5):
        assert b.place((row, col), WHITE)
    assert rules.winner(b.grid) == WHITE


def test_diagonal_backslash_win_black():
    # '\\' direction: (0,0),(1,1),(2,2),(3,3),(4,4)
    b = Board()
    for i in range(5):
        assert b.place((i, i), BLACK)
    assert rules.winner(b.grid) == BLACK


def test_diagonal_slash_win_white():
    # '/' direction: (0,4),(1,3),(2,2),(3,1),(4,0)
    b = Board()
    for i in range(5):
        assert b.place((i, 4 - i), WHITE)
    assert rules.winner(b.grid) == WHITE


def test_no_false_positive_with_gaps():
    b = Board()
    # XXXX _ X is not 5 consecutive
    row = 10
    for col in range(4):
        assert b.place((row, col), BLACK)
    assert b.place((row, 5), BLACK)
    assert rules.winner(b.grid) is None


def test_draw_on_full_small_grid_without_winner():
    # Use a 4x4 full grid: WIN_LENGTH=5 so winner must be None.
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
    b = Board()
    for i in range(5):
        assert b.place((0, i), BLACK)
    assert rules.is_terminal(b.grid) is True
    assert rules.is_draw(b.grid) is False
