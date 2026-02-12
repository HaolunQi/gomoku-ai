# gomoku-ai

Gomoku (15x15, five-in-a-row) with a clean separation between **game logic**, **agents**, and **pygame UI**.

---

## Quick Start

Clone the repository:

```bash
git clone https://github.com/HaolunQi/gomoku-ai.git
```

Enter the project directory:

```bash
cd gomoku-ai
```

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Run the Game (Pygame UI)

From the repository root (`gomoku-ai/`):

```bash
python src/main.py
```

In pygame mode:

* Human moves are made via **mouse clicks**
* `HumanAgent` (CLI-based) is **not used** in pygame (it relies on `input()`)

---

## CLI Tools

All CLI tools must be run from the project root:

```bash
cd gomoku-ai
```

---

### Run a Single Match

```bash
python scripts/run_match.py --black random --white greedy
```

Human vs agent:

```bash
python scripts/run_match.py --black human --white greedy --print-board
```

Options:

* `--black`, `--white`: agent names (`random`, `greedy`, `human`, etc.)
* `--seed N`: base RNG seed (white uses `seed + 1`)
* `--print-board`: print board after each move

---

### Using HumanAgent (CLI)

When using `HumanAgent`, moves are entered in the format:

```
row col
```

Example:

```
7 7
```

#### Exit HumanAgent

You can exit a CLI game in the following ways:

* **Ctrl + C** → Immediately terminate the program
* **Ctrl + D** (macOS/Linux) → Send EOF and exit input loop
* Close the terminal window

> `HumanAgent` is intended only for CLI interaction and is not used in pygame mode.

---

### Benchmark Agents

Run multiple games and aggregate results:

```bash
python scripts/benchmark.py --agents greedy random --games 200
```

Recommended (reduces first-move bias):

```bash
python scripts/benchmark.py --agents greedy random --games 200 --swap-sides --seed 0
```

Options:

* `--agents A B`: black and white agents
* `--games N`: number of games
* `--swap-sides`: alternate colors each game
* `--seed N`: reproducible randomness
* `--csv PATH`: write per-game results to CSV

---

## Project Structure

```
gomoku-ai/
  src/
    gomoku/     # Core game logic (board, rules, controller)
    agents/     # Agent implementations
    ui/         # Pygame UI
  tests/        # Pytest test suite
  scripts/      # Match runner and benchmarking tools
```

---

## Core Constants

The board size and win condition are defined in:

```
src/gomoku/board.py
```

```python
BOARD_SIZE = 15
WIN_LENGTH = 5
```

---

## Project Conventions

### 1. CI Scope (No UI in CI)

* CI tests game logic and agents only
* Pygame UI is intentionally excluded
* Keeps CI fast and platform-independent

---

### 2. HumanAgent Usage

* Intended only for CLI interaction
* Not used in pygame mode
* Not used in automated benchmarks

---

### 3. Player Control Is Symmetric

* Both Black and White can be agents or humans
* No hard-coded human side

---

### 4. Branching and Collaboration

* `main` is the stable branch
* Use feature branches for development
* Open pull requests before merging

---

### 5. Frozen Core APIs

The following interfaces are stable:

#### `Board`

* `place(move, stone)`
* `legal_moves()`
* `copy()`
* `grid`

#### `Agent`

* `select_move(board, stone)`

Do not change these without discussion.

---

### 6. Scripts vs Core Code

* `scripts/` is for experiments and benchmarking
* Core logic must live under `src/gomoku/` or `src/agents/`
* Core code must not depend on `scripts/`

---

## License

MIT (see `LICENSE`)

---
