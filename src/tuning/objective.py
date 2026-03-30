import time

from agents.ab_agent import AlphaBetaAgent
from gomoku.board import BLACK, WHITE
from gomoku.game import Game


def objective(weights, board_factory, opponents, games=4, time_penalty_weight=0.001):
    """Play the AB agent (with candidate weights) against opponents and return
    win_rate minus a small time penalty. Higher is better."""
    if not opponents:
        return 0.0

    ab_agent = AlphaBetaAgent(weights=weights)

    wins = 0
    total = 0
    total_ms = 0.0

    for opp in opponents:
        for i in range(games):
            board = board_factory()
            t0 = time.time()

            # swap colors each game so first-move advantage doesn't skew results
            if i % 2 == 0:
                game = Game(board=board, black_agent=ab_agent, white_agent=opp)
                ab_stone = BLACK
            else:
                game = Game(board=board, black_agent=opp, white_agent=ab_agent)
                ab_stone = WHITE

            # play the game out; move_cap is a safety net against infinite loops
            move_cap = board.size * board.size
            moves_played = 0
            while not game.is_over() and moves_played < move_cap:
                game.maybe_ai_move()
                moves_played += 1

            total_ms += (time.time() - t0) * 1000.0
            total += 1
            if game.winner() == ab_stone:
                wins += 1

    win_rate = wins / total if total > 0 else 0.0
    avg_ms = total_ms / total if total > 0 else 0.0
    return win_rate - time_penalty_weight * avg_ms
