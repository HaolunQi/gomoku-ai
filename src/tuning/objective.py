import time

from gomoku.board import BLACK

# TODO: fix import path if needed
try:
    from heuristics.evaluate import evaluate
except Exception:
    def evaluate(board, stone, weights=None):
        return 0.0


def objective(weights, board_factory, opponents, games=4, time_penalty_weight=0.001):
    # Objective: win rate vs baseline opponents + time penalty
    #
    # TODO: implement:
    #   - play games vs each opponent (swap colors)
    #   - measure wall-clock time per move or per game
    #   - compute win_rate - time_penalty_weight * avg_time_ms
    #
    # Scaffolding returns a stable float and measures minimal overhead.

    t0 = time.time()

    # Placeholder "score": just evaluate empty starting board once
    b0 = board_factory()
    _ = evaluate(b0, BLACK, weights)

    elapsed_ms = (time.time() - t0) * 1000.0
    return 0.0 - time_penalty_weight * float(elapsed_ms)
