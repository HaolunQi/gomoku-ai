# rl/train.py
# Self-play Q-learning training for the RL Gomoku agent.

import argparse
import csv
import json
import os
import random
import sys

from gomoku.board import Board, BLACK, WHITE
from gomoku import rules
from scripts.agent_loader import load_agent
from agents.rl_agent import RLAgent
from heuristics.features import extract_features


def save_weights(path, weights):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, sort_keys=True)


def load_weights(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def play_one_game(rl_agent, opponent, board_size, rl_stone):
    """Play one game: RL agent vs opponent.

    Returns (winner_stone_or_None, list_of_rl_transitions).
    Only collects transitions for the RL agent's moves.
    """
    board = Board(size=board_size)
    stone = BLACK
    rl_transitions = []

    while not rules.is_terminal(board.grid):
        board_before = board.copy()

        if stone == rl_stone:
            move = rl_agent.select_move(board, stone)
        else:
            move = opponent.select_move(board, stone)

        board.place(move, stone)
        next_stone = WHITE if stone == BLACK else BLACK
        done = rules.is_terminal(board.grid)

        # Only record RL agent's transitions
        if stone == rl_stone:
            rl_transitions.append(
                (board_before, stone, move, board.copy(), next_stone, done)
            )

        stone = next_stone

    w = rules.winner(board.grid)
    return w, rl_transitions


def assign_rewards(transitions, winner, rl_stone):
    """Assign shaped rewards to RL transitions.

    Logic:
    - if opponent has three-pressure and we do NOT have attack-ready shapes:
      reward defense only
    - otherwise:
      reward attack only
    - terminal bonus is added on top
    """
    rewarded = []

    for board_before, stone, move, next_board, next_stone, done in transitions:
        before_feats = extract_features(board_before, rl_stone)
        after_feats = extract_features(next_board, rl_stone)

        shaped = 0.0

        # ---------------------------------
        # 1. must defend three?
        # ---------------------------------
        opp_three_pressure = (
            before_feats.get("opp_live_three", 0.0)
            + before_feats.get("opp_jump_three", 0.0)
        )

        my_attack_ready = (
            before_feats.get("my_live_three", 0.0) > 0.0
            or before_feats.get("my_jump_three", 0.0) > 0.0
            or before_feats.get("my_live_four", 0.0) > 0.0
            or before_feats.get("my_blocked_four", 0.0) > 0.0
            or before_feats.get("my_jump_four", 0.0) > 0.0
        )

        must_defend_three = (opp_three_pressure > 0.0 and not my_attack_ready)

        if rules.winner(next_board.grid) == rl_stone:
            shaped += 10000.0

        # ---------------------------------
        # 2. defense mode
        # ---------------------------------
        if must_defend_three:
            if after_feats.get("opp_live_four", 0.0) < before_feats.get("opp_live_four", 0.0):
                shaped += 115.0

            if after_feats.get("opp_jump_four", 0.0) < before_feats.get("opp_jump_four", 0.0):
                shaped += 75.0

            if after_feats.get("opp_double_live_three", 0.0) < before_feats.get("opp_double_live_three", 0.0):
                shaped += 72.0

            if after_feats.get("opp_jump3_and_live3", 0.0) < before_feats.get("opp_jump3_and_live3", 0.0):
                shaped += 58.0

            if after_feats.get("opp_double_jump_three", 0.0) < before_feats.get("opp_double_jump_three", 0.0):
                shaped += 42.0

            if after_feats.get("opp_blocked_four", 0.0) < before_feats.get("opp_blocked_four", 0.0):
                shaped += 30.0

            if after_feats.get("opp_live_three", 0.0) < before_feats.get("opp_live_three", 0.0):
                shaped += 22.0

            if after_feats.get("opp_jump_three", 0.0) < before_feats.get("opp_jump_three", 0.0):
                shaped += 18.0

            if after_feats.get("opp_blocked_three", 0.0) < before_feats.get("opp_blocked_three", 0.0):
                shaped += 9.0

            if after_feats.get("opp_live_two", 0.0) < before_feats.get("opp_live_two", 0.0):
                shaped += 3.5

        # ---------------------------------
        # 3. attack mode
        # ---------------------------------
        else:
            if after_feats.get("my_live_four", 0.0) > before_feats.get("my_live_four", 0.0):
                shaped += 120.0

            if after_feats.get("my_jump_four", 0.0) > before_feats.get("my_jump_four", 0.0):
                shaped += 80.0

            if after_feats.get("my_double_live_three", 0.0) > before_feats.get("my_double_live_three", 0.0):
                shaped += 70.0

            if after_feats.get("my_jump3_and_live3", 0.0) > before_feats.get("my_jump3_and_live3", 0.0):
                shaped += 55.0

            if after_feats.get("my_double_jump_three", 0.0) > before_feats.get("my_double_jump_three", 0.0):
                shaped += 40.0

            if after_feats.get("my_blocked_four", 0.0) > before_feats.get("my_blocked_four", 0.0):
                shaped += 28.0

            if after_feats.get("my_live_three", 0.0) > before_feats.get("my_live_three", 0.0):
                shaped += 18.0

            if after_feats.get("my_jump_three", 0.0) > before_feats.get("my_jump_three", 0.0):
                shaped += 14.0

            if after_feats.get("my_blocked_three", 0.0) > before_feats.get("my_blocked_three", 0.0):
                shaped += 8.0

            if after_feats.get("my_live_two", 0.0) > before_feats.get("my_live_two", 0.0):
                shaped += 3.0

        # ---------------------------------
        # 4. terminal reward
        # ---------------------------------
        terminal = 0.0
        if done:
            if winner is None:
                terminal = 0.0
            elif winner == rl_stone:
                terminal = 1_000.0
            else:
                terminal = -1_000.0

        reward = shaped + terminal

        rewarded.append(
            (board_before, stone, move, reward, next_board, next_stone, done)
        )

    return rewarded


def train(
    out_path="weights_rl.json",
    episodes=5000,
    board_size=9,
    alpha=0.01,
    gamma=0.99,
    epsilon_start=1.0,
    epsilon_end=0.05,
    seed=0,
    log_interval=500,
    self_play=False,
    csv_log=None,
    opponent_type="random",
    init_weights_path=None,
):
    """Train an RL agent via Q-learning.

    opponent_type: "random", "greedy", or "self" for self-play.
    If csv_log is a path, writes training stats to CSV (useful for plotting).
    """
    if init_weights_path:
        print(f"Loading weights from {init_weights_path}")
        init_weights = load_weights(init_weights_path)
    else:
        init_weights = {}

    agent = RLAgent(
        weights=init_weights,
        alpha=alpha,
        gamma=gamma,
        epsilon=epsilon_start,
        seed=seed,
    )

    if opponent_type == "self" or self_play:
        opponent = agent
    else:
        opponent = load_agent(opponent_type, seed=seed)

    stats = {"wins": 0, "losses": 0, "draws": 0}
    rng = random.Random(seed)

    csv_file = None
    csv_writer = None
    if csv_log:
        csv_file = open(csv_log, "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["episode", "epsilon", "wins", "losses", "draws", "win_rate"])

    for ep in range(1, episodes + 1):
        progress = ep / episodes
        agent.epsilon = epsilon_start + (epsilon_end - epsilon_start) * progress

        rl_stone = BLACK if ep % 2 == 0 else WHITE

        winner, transitions = play_one_game(agent, opponent, board_size, rl_stone)
        rewarded = assign_rewards(transitions, winner, rl_stone)

        for board_b, stone, move, reward, next_board, next_stone, done in rewarded:
            agent.update(board_b, stone, move, reward, next_board, next_stone, done)

        if winner == rl_stone:
            stats["wins"] += 1
        elif winner is None:
            stats["draws"] += 1
        else:
            stats["losses"] += 1

        if ep % log_interval == 0:
            total = stats["wins"] + stats["losses"] + stats["draws"]
            win_rate = stats["wins"] / total if total > 0 else 0.0
            print(
                f"Episode {ep}/{episodes} | "
                f"epsilon={agent.epsilon:.3f} | "
                f"W:{stats['wins']} L:{stats['losses']} D:{stats['draws']} | "
                f"win_rate={win_rate:.1%}"
            )
            if csv_writer:
                csv_writer.writerow([
                    ep, f"{agent.epsilon:.3f}",
                    stats["wins"], stats["losses"], stats["draws"],
                    f"{win_rate:.4f}",
                ])
            stats = {"wins": 0, "losses": 0, "draws": 0}

    if csv_file:
        csv_file.close()
        print(f"Training log saved to {csv_log}")

    save_weights(out_path, agent.weights)
    print(f"Weights saved to {out_path}")
    return agent.weights


def evaluate_vs(weights_path, opponent_type="random", board_size=9, games=100, seed=42):
    """Evaluate trained RL agent vs a given opponent type."""
    weights = load_weights(weights_path)
    rl = RLAgent(weights=weights, epsilon=0.0, seed=seed)

    opp = load_agent(opponent_type, seed=seed)
    opp_name = getattr(opp, "name", opponent_type)

    rl_wins = 0
    opp_wins = 0
    draws = 0

    for g in range(games):
        board = Board(size=board_size)
        if g % 2 == 0:
            agents = {BLACK: rl, WHITE: opp}
            rl_stone = BLACK
        else:
            agents = {BLACK: opp, WHITE: rl}
            rl_stone = WHITE

        stone = BLACK
        while not rules.is_terminal(board.grid):
            move = agents[stone].select_move(board, stone)
            board.place(move, stone)
            stone = WHITE if stone == BLACK else BLACK

        w = rules.winner(board.grid)
        if w == rl_stone:
            rl_wins += 1
        elif w is None:
            draws += 1
        else:
            opp_wins += 1

    print(f"RL vs {opp_name} ({board_size}x{board_size}, {games} games): "
          f"RL wins {rl_wins}, {opp_name} wins {opp_wins}, Draws {draws} "
          f"({100*rl_wins/games:.1f}% win rate)")
    return rl_wins, opp_wins, draws


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train RL Gomoku agent")
    parser.add_argument("--episodes", type=int, default=5000)
    parser.add_argument("--board-size", type=int, default=9)
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--out", default="weights_rl.json")
    parser.add_argument("--eval", action="store_true", help="Evaluate after training")
    parser.add_argument("--eval-only", type=str, default=None, help="Skip training, evaluate this weights file")
    parser.add_argument("--csv-log", type=str, default=None, help="Save training stats to CSV")
    parser.add_argument("--opponent", type=str, default="random", help="Opponent agent name ")
    parser.add_argument("--init-weights", type=str, default=None, help="Path to initial weights")
    parser.add_argument("--eval-opponents", nargs="+", default=["random", "greedy"], help="Opponent agents to evaluate against",)
    args = parser.parse_args()

    if args.eval_only:
        for opp_name in args.eval_opponents:
            evaluate_vs(args.eval_only, opp_name, board_size=args.board_size)
    else:
        train(
            out_path=args.out,
            episodes=args.episodes,
            board_size=args.board_size,
            alpha=args.alpha,
            gamma=args.gamma,
            csv_log=args.csv_log,
            opponent_type=args.opponent,
        )
        if args.eval:
            for opp_name in args.eval_opponents:
                evaluate_vs(args.out, opp_name, board_size=args.board_size)
