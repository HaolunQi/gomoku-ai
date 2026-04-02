from gomoku.board import Board
from gomoku.game import Game
from agents.random_agent import RandomAgent
from agents.greedy_agent import GreedyAgent
from agents.ab_agent import AlphaBetaAgent
from agents.rl_agent import RLAgent
from ui.pygame_ui import PygameUI
from pathlib import Path
import json


# - Human (UI) vs Agent:
#     Game(board=Board(), white_agent=RandomAgent())
#     Game(board=Board(), black_agent=RandomAgent())
#
# - Human (UI) vs Human (UI):
#     Game(board=Board())
#
# - Agent vs Human (UI):
#     Game(board=Board(), white_agent=RandomAgent())
#     Game(board=Board(), black_agent=RandomAgent())
#
# - Agent vs Agent (watch-only):
#     Game(board=Board(), black_agent=AlphaBetaAgent(), white_agent=AlphaBetaAgent())
#     Game(board=Board(), black_agent=RLAgent(weights=weights), white_agent=RLAgent(weights=weights))
#
# 
def load_weights(filename):
    path = Path(__file__).resolve().parents[1] / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

weights = load_weights("rl_weights.json")

def main():
    game = Game(board=Board(), black_agent=AlphaBetaAgent(), white_agent=AlphaBetaAgent())
    PygameUI().run(game)

if __name__ == "__main__":
    main()
