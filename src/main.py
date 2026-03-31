from gomoku.board import Board
from gomoku.game import Game
from agents.random_agent import RandomAgent
from agents.ab_agent import AlphaBetaAgent
from agents.rl_agent import RLAgent
from ui.pygame_ui import PygameUI

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
#     Game(board=Board(), black_agent=RandomAgent(), white_agent=RandomAgent())
def main():
    game = Game(board=Board(), white_agent=AlphaBetaAgent())
    PygameUI().run(game)

if __name__ == "__main__":
    main()
