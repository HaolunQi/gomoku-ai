from abc import ABC, abstractmethod


class Agent(ABC):
    name = "agent"  # used by agent loader

    @abstractmethod
    def select_move(self, board, stone):
        raise NotImplementedError