import random
from agents.base import Agent


class RandomAgent(Agent):
    # Baseline agent: choose a random legal move

    name = "random"

    def __init__(self, seed=None):
        # Initialize local RNG for reproducibility
        self._rng = random.Random(seed)

    def select_move(self, board, stone):
        # Choose uniformly from legal moves
        moves = board.legal_moves()
        if not moves:
            raise RuntimeError("No legal moves available (game is over).")
        return self._rng.choice(moves)
