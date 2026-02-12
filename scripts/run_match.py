import argparse
import sys
from pathlib import Path

# Ensure src/ is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gomoku.board import Board, BLACK, WHITE
from gomoku.game import Game
from gomoku import rules

from agent_loader import load_agent


def play_match(black_name, white_name, seed=None, print_board=False, max_illegal_retries=3):
    # Run a single match and return winner or None for draw

    black_agent = load_agent(black_name, seed=seed)
    white_agent = load_agent(white_name, seed=None if seed is None else seed + 1)

    game = Game(board=Board(), black_agent=black_agent, white_agent=white_agent, to_move=BLACK)

    illegal_streak = 0

    while not game.is_over():
        agent = game.agent_for_turn()
        assert agent is not None

        move = agent.select_move(game.board, game.to_move)
        ok = game.step(move)

        if not ok:
            illegal_streak += 1
            if illegal_streak >= max_illegal_retries:
                raise RuntimeError(
                    f"Agent {agent.__class__.__name__} produced illegal moves repeatedly."
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


def main():
    # CLI entry point for single match
    parser = argparse.ArgumentParser(description="Run a single Gomoku match (CLI).")
    parser.add_argument("--black", default="random")
    parser.add_argument("--white", default="greedy")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--print-board", action="store_true")
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
