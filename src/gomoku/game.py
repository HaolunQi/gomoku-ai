from gomoku.board import BLACK, WHITE
from . import rules


class Game:
    def __init__(self, board, black_agent=None, white_agent=None, to_move=BLACK):
        # Initialize game state and agents
        self.board = board
        self.black_agent = black_agent
        self.white_agent = white_agent
        self.to_move = to_move

    def other(self, stone):
        # Return the opponent's stone
        return WHITE if stone == BLACK else BLACK

    def step(self, move):
        # Execute one move for the current player
        if self.board.place(move, self.to_move):
            self.to_move = self.other(self.to_move)
            return True
        return False

    def winner(self):
        # Return the winning stone if any
        return rules.winner(self.board.grid)

    def is_over(self):
        # Return True if the game has ended
        return rules.is_terminal(self.board.grid)

    def agent_for_turn(self):
        # Return the agent responsible for current turn
        return self.black_agent if self.to_move == BLACK else self.white_agent

    def maybe_ai_move(self):
        # If AI turn and game not over, select and apply a move
        if self.is_over():
            return False

        agent = self.agent_for_turn()
        if agent is None:
            return False

        move = agent.select_move(self.board, self.to_move)
        return self.step(move)
