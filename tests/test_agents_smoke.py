import builtins
import pytest

from gomoku.board import Board, BLACK, WHITE
from gomoku import rules

from agents.random_agent import RandomAgent
from agents.greedy_agent import GreedyAgent
from agents.human_agent import HumanAgent


def test_random_agent_returns_legal_move():
    b = Board()
    agent = RandomAgent(seed=0)
    move = agent.select_move(b, BLACK)
    assert b.in_bounds(move)
    assert b.is_empty(move)
    # After placing it should no longer be empty.
    assert b.place(move, BLACK)
    assert rules.winner(b.grid) in (None, BLACK)


def test_greedy_agent_wins_if_possible():
    b = Board()
    # Create four-in-a-row for BLACK at row 7, cols 0..3; winning move is (7,4)
    row = 7
    for col in range(4):
        assert b.place((row, col), BLACK)
    agent = GreedyAgent()
    move = agent.select_move(b, BLACK)
    assert move == (row, 4)
    assert b.place(move, BLACK)
    assert rules.winner(b.grid) == BLACK


def test_greedy_agent_blocks_opponents_immediate_win():
    b = Board()
    # WHITE has four-in-a-row; BLACK must block.
    row = 10
    for col in range(4):
        assert b.place((row, col), WHITE)
    agent = GreedyAgent()
    move = agent.select_move(b, BLACK)
    assert move == (row, 4)


def test_human_agent_accepts_valid_move(monkeypatch):
    b = Board()
    agent = HumanAgent(prompt="")

    # Provide a few invalid inputs, then a valid one.
    inputs = iter([
        "",          # empty
        "7",         # not two ints
        "a b",       # not ints
        "99 99",     # out of bounds
        "3 3",       # valid
    ])

    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    move = agent.select_move(b, BLACK)
    assert move == (3, 3)


def test_human_agent_rejects_occupied_cell(monkeypatch):
    b = Board()
    assert b.place((2, 2), WHITE)
    agent = HumanAgent(prompt="")

    inputs = iter([
        "2 2",  # occupied
        "2 3",  # valid
    ])

    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    move = agent.select_move(b, BLACK)
    assert move == (2, 3)
