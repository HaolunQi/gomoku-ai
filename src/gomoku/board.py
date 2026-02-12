BOARD_SIZE = 15
WIN_LENGTH = 5
BLACK = "X"
WHITE = "O"
EMPTY = " "


class Board:
    def __init__(self, size=BOARD_SIZE):
        # Initialize an empty board
        self.size = size
        self._grid = [[EMPTY] * size for _ in range(size)]
        self.last_move = None

    @property
    def grid(self):
        # Return an immutable view of the grid
        return tuple(tuple(row) for row in self._grid)

    def in_bounds(self, move):
        # Check whether move is inside board boundaries
        r, c = move
        return 0 <= r < self.size and 0 <= c < self.size

    def is_empty(self, move):
        # Check whether position is empty
        if not self.in_bounds(move):
            return False
        r, c = move
        return self._grid[r][c] == EMPTY

    def place(self, move, stone):
        # Place a stone if the move is legal
        if not self.is_empty(move):
            return False
        r, c = move
        self._grid[r][c] = stone
        self.last_move = move
        return True

    def legal_moves(self):
        # Return all currently legal moves
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self._grid[r][c] == EMPTY
        ]

    def copy(self):
        # Return a deep copy of the board
        b = Board(self.size)
        b._grid = [row[:] for row in self._grid]
        b.last_move = self.last_move
        return b

    def __str__(self):
        # Return a formatted string of the board
        header = "   " + " ".join(f"{c:2d}" for c in range(self.size))
        lines = [header]
        for r in range(self.size):
            row = " ".join(f"{(v if v != EMPTY else '.'):>2}" for v in self._grid[r])
            lines.append(f"{r:2d} {row}")
        return "\n".join(lines)
