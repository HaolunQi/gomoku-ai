import argparse
import csv
import sys
from pathlib import Path

# Ensure src/ is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gomoku.board import BLACK, WHITE
from scripts.run_match import play_match


class Stats:
    # Tracks aggregate benchmark statistics

    def __init__(self):
        self.games = 0
        self.black_wins = 0
        self.white_wins = 0
        self.draws = 0

    def record(self, winner):
        # Update counters based on winner
        self.games += 1
        if winner == BLACK:
            self.black_wins += 1
        elif winner == WHITE:
            self.white_wins += 1
        else:
            self.draws += 1


def _pct(x, total):
    # Return percentage string
    if total == 0:
        return "0.0%"
    return f"{(100.0 * x / total):.1f}%"


def run_benchmark(black, white, games, seed=None, swap_sides=False, csv_path=None):
    # Run N matches and collect stats
    stats = Stats()
    rows = []

    for i in range(games):
        if swap_sides and (i % 2 == 1):
            b_name, w_name = white, black
        else:
            b_name, w_name = black, white

        game_seed = None if seed is None else seed + i * 1000

        winner = play_match(b_name, w_name, seed=game_seed, print_board=False)
        stats.record(winner)

        if csv_path is not None:
            if winner == BLACK:
                outcome = "BLACK"
            elif winner == WHITE:
                outcome = "WHITE"
            else:
                outcome = "DRAW"
            rows.append((i, b_name, w_name, outcome))

    if csv_path is not None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["game", "black_agent", "white_agent", "result"])
            writer.writerows(rows)

    return stats


def main():
    # CLI entry point for benchmarking
    parser = argparse.ArgumentParser(description="Benchmark Gomoku agents (no UI).")

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--agents", nargs=2, metavar=("BLACK", "WHITE"))

    parser.add_argument("--black", default=None)
    parser.add_argument("--white", default=None)
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--swap-sides", action="store_true")
    parser.add_argument("--csv", default=None)

    args = parser.parse_args()

    if args.agents:
        black_name, white_name = args.agents
    else:
        black_name = args.black or "random"
        white_name = args.white or "greedy"

    csv_path = Path(args.csv) if args.csv else None

    try:
        stats = run_benchmark(
            black=black_name,
            white=white_name,
            games=args.games,
            seed=args.seed,
            swap_sides=args.swap_sides,
            csv_path=csv_path,
        )
    except Exception as e:
        print(f"Benchmark failed: {e}", file=sys.stderr)
        return 1

    print("Benchmark complete")
    print(f"  Black agent: {black_name}")
    print(f"  White agent: {white_name}")
    print(f"  Games:       {stats.games}")
    print(f"  Black wins:  {stats.black_wins} ({_pct(stats.black_wins, stats.games)})")
    print(f"  White wins:  {stats.white_wins} ({_pct(stats.white_wins, stats.games)})")
    print(f"  Draws:       {stats.draws} ({_pct(stats.draws, stats.games)})")

    if csv_path is not None:
        print(f"  CSV:         {csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
