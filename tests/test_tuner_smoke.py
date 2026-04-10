import os
import tempfile

from agents.random_agent import RandomAgent
from gomoku.board import Board

from tuning.local_search_tuner import LocalSearchTuner
from tuning.objective import objective

# tests/test_tuner_smoke.py
# Smoke tests for the local search tuning pipeline.
def test_objective_returns_float_with_real_opponent():
    # run a couple of real games on a tiny board and check the score is a valid float
    score = objective(
        weights={"my_stones": 1.0, "opp_stones": -1.0, "empty": 0.0},
        board_factory=lambda: Board(size=6),
        opponents=[RandomAgent(seed=0)],
        games=2,
    )
    assert isinstance(score, float)
    assert score <= 1.0


def test_tuner_writes_and_reads_weights_file():
    tuner = LocalSearchTuner(rng_seed=0)

    def board_factory():
        return Board()

    opponents = []  # TODO: plug in baseline opponents later

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "weights.json")
        w0 = {"my_stones": 1.0, "opp_stones": -1.0}
        w1 = tuner.tune(w0, board_factory, opponents, out_path=path, iters=0, restarts=0)
        assert os.path.exists(path)
        w2 = tuner.load(path)
        assert isinstance(w1, dict)
        assert isinstance(w2, dict)
