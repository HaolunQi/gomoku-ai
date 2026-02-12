import os
import tempfile

from gomoku.board import Board

from tuning.local_search_tuner import LocalSearchTuner


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
