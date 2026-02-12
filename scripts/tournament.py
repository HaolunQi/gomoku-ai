import random

from gomoku.board import Board, BLACK, WHITE
from gomoku import rules

# TODO: fix import path if needed
try:
    from agents.random_agent import RandomAgent
    from agents.greedy_agent import GreedyAgent
except Exception:
    RandomAgent = None
    GreedyAgent = None


def other(stone):
    return WHITE if stone == BLACK else BLACK


def play_game(board, black_agent, white_agent, max_moves=400):
    # Minimal deterministic game runner for experiments (no UI)
    #
    # TODO: add:
    #   - time per move tracking
    #   - illegal-move handling policy
    #   - optional opening rules / small board settings
    to_move = BLACK
    for _ in range(int(max_moves)):
        if rules.is_terminal(board.grid):
            break
        agent = black_agent if to_move == BLACK else white_agent
        move = agent.select_move(board, to_move)
        ok = board.place(move, to_move)
        if not ok:
            # TODO: define penalty policy (for now: resign)
            return other(to_move)
        to_move = other(to_move)

    return rules.winner(board.grid)  # None if draw


def round_robin(agents, games_per_pair=2, seed=0):
    # Returns results dict keyed by agent.name
    rng = random.Random(seed)
    results = {a.name: {"wins": 0, "losses": 0, "draws": 0} for a in agents}

    # TODO: include color swap and reproducible openings
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a = agents[i]
            b = agents[j]
            for g in range(int(games_per_pair)):
                board = Board()
                # Alternate colors
                if g % 2 == 0:
                    w = play_game(board, a, b)
                    black_name, white_name = a.name, b.name
                else:
                    w = play_game(board, b, a)
                    black_name, white_name = b.name, a.name

                if w is None:
                    results[a.name]["draws"] += 1
                    results[b.name]["draws"] += 1
                elif w == BLACK:
                    results[black_name]["wins"] += 1
                    results[white_name]["losses"] += 1
                else:
                    results[white_name]["wins"] += 1
                    results[black_name]["losses"] += 1

    return results


def default_agent_pool():
    # Convenience for quick runs
    pool = []
    if RandomAgent is not None:
        pool.append(RandomAgent(seed=0))
    if GreedyAgent is not None:
        pool.append(GreedyAgent())
    # TODO: add AlphaBetaAgent and RLAgent imports here when ready
    return pool
