from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .board import Board, BLACK, WHITE, Stone, Move
from . import rules

from agents.base import Agent 

def other(stone: Stone) -> Stone:
    """Return the opponent's stone."""
    return WHITE if stone == BLACK else BLACK


@dataclass
class Game:
    """Game controller: manages turns, agents, and delegates to Board and Rules."""
    board: Board
    black_agent: Optional[Agent] = None
    white_agent: Optional[Agent] = None
    to_move: str = BLACK  # Black moves first

    def step(self, move: Move) -> bool:
        """
        Execute one move for the current player.
        Returns True if the move is legal and applied; False otherwise.
        """
        ok = self.board.place(move, self.to_move)
        if ok:
            self.to_move = other(self.to_move)
        return ok

    def winner(self) -> Stone | None:
        """Return the winning stone, or None if there is no winner."""
        return rules.winner(self.board.grid)

    def is_over(self) -> bool:
        """Return True iff the game has ended (win or draw)."""
        return rules.is_terminal(self.board.grid)

    def agent_for_turn(self) -> Optional[Agent]:
        """Return the agent for the side to move, or None if human-controlled."""
        return self.black_agent if self.to_move == BLACK else self.white_agent

    def maybe_ai_move(self) -> bool:
        """
        If it's an AI-controlled turn and game is not over,
        ask the agent to select a move and apply it.

        Returns True iff an AI move was made.
        """
        if self.is_over():
            return False

        agent = self.agent_for_turn()
        if agent is None:
            return False

        move = agent.select_move(self.board, self.to_move)
        return self.step(move)
