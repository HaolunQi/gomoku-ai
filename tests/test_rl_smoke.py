# tests/test_rl_smoke.py
import os
import tempfile

from gomoku.board import Board, BLACK

from agents.rl_agent import RLAgent
from rl.train import train_self_play, load_weights


def test_rl_agent_import_and_legal_move():
    b = Board()
    a = RLAgent(weights={"my_stones": 1.0}, epsilon=0.0, seed=0)
    m = a.select_move(b, BLACK)
    assert b.in_bounds(m)
    assert b.is_empty(m)


def test_rl_train_writes_weights_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "w.json")
        train_self_play(out_path=path, episodes=1, seed=0)
        w = load_weights(path)
        assert isinstance(w, dict)
        assert "my_stones" in w
