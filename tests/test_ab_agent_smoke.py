from gomoku.board import Board, BLACK
from gomoku import rules

from agents.ab_agent import AlphaBetaAgent


def test_ab_agent_import_and_legal_move():
    b = Board()
    a = AlphaBetaAgent(max_depth=1, node_budget=10, time_budget_ms=10)
    m = a.select_move(b, BLACK)
    assert b.in_bounds(m)
    assert b.is_empty(m)
    assert b.place(m, BLACK)
    assert rules.winner(b.grid) in (None, BLACK)
