from gomoku.board import Board, BLACK

from heuristics.features import extract_features
from heuristics.evaluate import evaluate


def test_features_and_evaluate_importable_and_return_types():
    b = Board()
    feats = extract_features(b, BLACK)
    assert isinstance(feats, dict)
    s = evaluate(b, BLACK, weights={"my_stones": 1.0})
    assert isinstance(s, float)
