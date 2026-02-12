from abc import ABC, abstractmethod


class Agent(ABC):
    # Base class for all agents

    name = "agent"

    @abstractmethod
    def select_move(self, board, stone):
        # Return the selected move for the given board and stone
        raise NotImplementedError
