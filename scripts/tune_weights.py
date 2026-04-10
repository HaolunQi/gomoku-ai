import argparse
import sys
from pathlib import Path
# tests/test_tuner_smoke.py
# Smoke tests for the local search tuning pipeline.
# claude was used for the arguments

# Ensure src/ is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents.greedy_agent import GreedyAgent
from agents.random_agent import RandomAgent
from gomoku.board import Board
from heuristics.evaluate import DEFAULT_WEIGHTS
from tuning.local_search_tuner import LocalSearchTuner
from tuning.objective import objective


def main():
    parser = argparse.ArgumentParser(description="Tune heuristic weights using hill climbing.")
    parser.add_argument("--iters", type=int, default=50, help="Hill-climbing steps per restart")
    parser.add_argument("--restarts", type=int, default=2, help="Number of random restarts")
    parser.add_argument("--games", type=int, default=4, help="Games per opponent per weight eval")
    parser.add_argument("--board-size", type=int, default=9, help="Board size to tune on")
    parser.add_argument("--out", default="data/weights.json", help="Output path for best weights")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed for reproducibility")
    args = parser.parse_args()

    board_factory = lambda: Board(size=args.board_size)
    opponents = [RandomAgent(seed=args.seed), GreedyAgent()]

    tuner = LocalSearchTuner(rng_seed=args.seed)
    initial_weights = dict(DEFAULT_WEIGHTS)

    print(f"Tuning on {args.board_size}x{args.board_size} board")
    print(f"  iters={args.iters}, restarts={args.restarts}, games={args.games}")
    print(f"  opponents: {[type(o).__name__ for o in opponents]}")
    print()

    best_weights = tuner.tune(
        initial_weights=initial_weights,
        board_factory=board_factory,
        opponents=opponents,
        out_path=args.out,
        iters=args.iters,
        restarts=args.restarts,
        games=args.games,
    )

    best_score = objective(best_weights, board_factory, opponents, games=args.games)
    print(f"Best score: {best_score:.4f}")
    print(f"Weights saved to: {args.out}")
    for k, v in sorted(best_weights.items()):
        print(f"  {k}: {v:.4f}")


if __name__ == "__main__":
    main()
