from __future__ import annotations
from dataclasses import dataclass
from typing import Final, List, Literal, Tuple, TypeAlias

BOARD_SIZE = 15
WIN_LENGTH = 5
BLACK: Final = 'X'
WHITE: Final = 'O'
EMPTY: Final = ' '
Stone: TypeAlias = Literal['X', 'O']
Move: TypeAlias = Tuple[int, int]  # Board coordinate (row, col)

@dataclass
class Board:
    size: int = BOARD_SIZE

    def __post_init__(self) -> None:
        """ Initialize an empty size x size board and the last move """
        self._grid: List[List[str]] = [[EMPTY] * self.size for _ in range(self.size)]
        self.last_move: Move | None = None

    @property
    def grid(self) -> tuple[tuple[str, ...], ...]:
        """Read-only view of the board grid."""
        return tuple(tuple(row) for row in self._grid)


    def in_bounds(self, move: Move) -> bool:
        """ Check whether a move is within board boundaries """
        row, col = move
        return 0 <= row < self.size and 0 <= col < self.size

    def is_empty(self, move: Move) -> bool:
        """ Check whether a position is empty """
        row, col = move
        return self._grid[row][col] == EMPTY

    def place(self, move: Move, stone: str) -> bool:
        """
        Place a stone on the board.
        Returns True if the move is legal; False otherwise.
        """
        if not self.in_bounds(move):
            return False
        if not self.is_empty(move):
            return False
        row, col = move
        self._grid[row][col] = stone
        self.last_move = move
        return True

    def legal_moves(self) -> List[Move]:
        """ Return all currently legal moves """
        moves: List[Move] = []
        for row in range(self.size):
            for col in range(self.size):
                if self._grid[row][col] == EMPTY:
                    moves.append((row, col))
        return moves

    def copy(self) -> "Board":
        """ Create a deep copy of the board """
        b = Board(self.size)
        b._grid = [row[:] for row in self._grid]
        b.last_move = self.last_move
        return b
    
    def __str__(self) -> str:
        """Print the board """
        header = "   " + " ".join(f"{c:2d}" for c in range(self.size))
        lines = [header]
        for r in range(self.size):
            row = " ".join(
                f"{(self._grid[r][c] if self._grid[r][c] != EMPTY else '.'):>2}"
                for c in range(self.size))
            lines.append(f"{r:2d} {row}")
        return "\n".join(lines)