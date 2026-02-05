from gomoku.board import Board, BLACK, WHITE, EMPTY, BOARD_SIZE


def test_board_initial_state():
    b = Board()
    assert b.size == BOARD_SIZE
    assert b.last_move is None
    # grid is read-only view (tuple of tuples) and all EMPTY
    assert isinstance(b.grid, tuple)
    assert len(b.grid) == BOARD_SIZE
    assert all(len(row) == BOARD_SIZE for row in b.grid)
    assert all(cell == EMPTY for row in b.grid for cell in row)


def test_in_bounds_and_is_empty():
    b = Board()
    assert b.in_bounds((0, 0))
    assert b.in_bounds((14, 14))
    assert not b.in_bounds((-1, 0))
    assert not b.in_bounds((0, 15))
    assert b.is_empty((7, 7))
    b.place((7, 7), BLACK)
    assert not b.is_empty((7, 7))


def test_place_updates_grid_and_last_move():
    b = Board()
    assert b.place((1, 2), BLACK) is True
    assert b.grid[1][2] == BLACK
    assert b.last_move == (1, 2)


def test_place_rejects_out_of_bounds_and_occupied():
    b = Board()
    assert b.place((-1, 0), BLACK) is False
    assert b.last_move is None
    assert b.place((0, 15), BLACK) is False
    assert b.last_move is None

    assert b.place((3, 3), WHITE) is True
    assert b.place((3, 3), BLACK) is False
    # last_move should remain the last successful move
    assert b.last_move == (3, 3)


def test_legal_moves_count_and_contents():
    b = Board()
    moves = b.legal_moves()
    assert len(moves) == BOARD_SIZE * BOARD_SIZE
    assert (0, 0) in moves and (14, 14) in moves
    b.place((0, 0), BLACK)
    b.place((14, 14), WHITE)
    moves2 = b.legal_moves()
    assert len(moves2) == BOARD_SIZE * BOARD_SIZE - 2
    assert (0, 0) not in moves2 and (14, 14) not in moves2


def test_copy_is_deep_and_preserves_last_move():
    b = Board()
    b.place((5, 6), BLACK)
    b2 = b.copy()
    assert b2 is not b
    assert b2.grid == b.grid
    assert b2.last_move == b.last_move

    # Mutate copy, original unchanged
    assert b2.place((0, 0), WHITE)
    assert b2.grid[0][0] == WHITE
    assert b.grid[0][0] == EMPTY
