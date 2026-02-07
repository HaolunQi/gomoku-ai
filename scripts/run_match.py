#!/usr/bin/env python3
"""Run a single Gomoku match (CLI, no UI).

Examples:
  python scripts/run_match.py --black random --white greedy
  python scripts/run_match.py --black human --white greedy --print-board

This script is meant for quick manual runs and CI smoke checks.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# Ensure `src/` is importable when running from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gomoku.board import Board, BLACK, WHITE, Stone
from gomoku.game import Game
from gomoku import rules

from agent_loader import load_agent

def play_match(
    black_name: str,
    white_name: str,
    seed: Optional[int] = None,
    print_board: bool = False,
    max_illegal_retries: int = 3,
) -> Stone | None:
    """Run one match; return winner stone ('X'/'O') or None for draw."""

    black_agent = load_agent(black_name, seed=seed)
    # Use a different seed stream for white random to avoid identical play.
    white_agent = load_agent(white_name, seed=None if seed is None else seed + 1)

    game = Game(board=Board(), black_agent=black_agent, white_agent=white_agent, to_move=BLACK)

    illegal_streak = 0
    while not game.is_over():
        agent = game.agent_for_turn()
        assert agent is not None, "This script expects both sides to have agents (use HumanAgent for human input)."

        move = agent.select_move(game.board, game.to_move)
        ok = game.step(move)
        if not ok:
            illegal_streak += 1
            if illegal_streak >= max_illegal_retries:
                raise RuntimeError(
                    f"Agent {agent.__class__.__name__} produced illegal moves {illegal_streak} times in a row."
                )
        else:
            illegal_streak = 0
        
        if print_board:
            print(game.board)
            print()

    w = game.winner()
    if w is None and rules.is_draw(game.board.grid):
        return None
    return w


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a single Gomoku match (CLI).")
    parser.add_argument("--black", default="random", help="black agent: random|greedy|human")
    parser.add_argument("--white", default="greedy", help="white agent: random|greedy|human")
    parser.add_argument("--seed", type=int, default=None, help="seed for RandomAgent (black uses seed, white uses seed+1)")
    parser.add_argument("--print-board", action="store_true", help="print board after each move")
    args = parser.parse_args()

    try:
        w = play_match(args.black, args.white, seed=args.seed, print_board=args.print_board)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 3

    if w == BLACK:
        print(f"Winner: BLACK ({args.black})")
    elif w == WHITE:
        print(f"Winner: WHITE ({args.white})")
    else:
        print("Result: DRAW")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
