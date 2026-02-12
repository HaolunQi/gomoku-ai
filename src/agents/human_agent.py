from agents.base import Agent


class HumanAgent(Agent):
    # Human-controlled agent via stdin

    name = "human"

    def __init__(self, prompt=None):
        # Initialize the input prompt
        self._prompt = prompt or "Enter move as: row col (0-indexed): "

    def select_move(self, board, stone):
        # Prompt until a legal move is entered
        while True:
            try:
                raw = input(self._prompt).strip()
            except EOFError as e:
                raise RuntimeError("No input available for HumanAgent.") from e

            if not raw:
                print("Empty input. Example: 7 7")
                continue

            parts = raw.replace(",", " ").split()
            if len(parts) != 2:
                print("Please enter exactly two integers: row col (e.g., 7 7)")
                continue

            try:
                row = int(parts[0])
                col = int(parts[1])
            except ValueError:
                print("Invalid integers. Example: 7 7")
                continue

            move = (row, col)
            if not board.in_bounds(move):
                print(f"Out of bounds. Valid range: 0..{board.size - 1}")
                continue
            if not board.is_empty(move):
                print("That cell is occupied. Try again.")
                continue

            return move
