# gomoku-ai

Gomoku (15x15, five-in-a-row) with a clean separation between **game logic**, **agents**, and **pygame UI**.

## Quick start

Requires **Python 3.14+**.

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

## Running Tests

Run the test suite from the project root:

```bash
pytest
```

### Pygame UI (human via mouse; agents optional)

```bash
python src/main.py
```

> In pygame mode, **mouse clicks** provide human moves. `HumanAgent` (CLI-based) is **not** used in pygame because it calls `input()`.

## Project structure

- `src/gomoku/`: board + rules + game controller
- `src/agents/`: agent implementations
- `src/ui/`: pygame UI
- `tests/`: pytest tests
- `scripts/`: match runner + benchmark tooling

## CLI Tools

### Run a single match (`scripts/run_match.py`)

Run one Gomoku game in the terminal.

```bash
python /scripts/run_match.py --black random --white greedy
```

Human vs agent:

```bash
python /scripts/run_match.py --black human --white greedy --print-board
```

Options:

* `--black`, `--white`: agent names (e.g. `random`, `greedy`, `human`)
* `--seed N`: base RNG seed (white uses `seed + 1`)
* `--print-board`: print board after each move

> Note: Command-line flags (--...) may appear in any order.

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

### Benchmark agents (`scripts/benchmark.py`)

Run many games and aggregate results.

```bash
python /scripts/benchmark.py --agents greedy random --games 200
```

Recommended (reduces first-move bias):

```bash
python /scripts/benchmark.py --agents greedy random --games 200 --swap-sides --seed 0
```

Options:

* `--agents A B`: black and white agents
* `--games N`: number of games
* `--swap-sides`: alternate colors each game
* `--seed N`: reproducible randomness
* `--csv PATH`: write per-game results to CSV

> Note: Command-line flags (--...) may appear in any order.

---

### Agent discovery

Agents are selected by their class attribute `name`:

```python
class RandomAgent(Agent):
    name = "random"
```

Any agent under `agents/` with a unique `name` is automatically loaded by the scripts.

## Project Conventions

### 1. CI Scope (No UI in CI)
- Continuous Integration (CI) **tests game logic and agents only**.
- The pygame UI is **intentionally excluded** from CI.
- This avoids platform-specific issues and keeps CI fast and reliable.

---

### 2. HumanAgent Usage
- `HumanAgent` is **only intended for CLI-based interaction**.
- It is **not used** in the pygame UI or automated benchmarks.

---

### 3. Player Control Is Symmetric
- **Both Black and White can be controlled by agents or humans.**
- There is no hard-coded assumption that one side must be human-controlled.

---

### 4. Branching and Collaboration
- `main` is the **stable branch**.
- Please use **feature branches** for development and open PRs for merging.
- Avoid pushing large or experimental changes directly to `main`.

---

### 5. Testing Philosophy
- Tests focus on **correctness**, not UI behavior or performance.
- We do not test pygame interactions in automated tests.
- Performance evaluation is handled via scripts.

---

### 6. Frozen Core APIs
- The public APIs of `Board` and `Agent` are considered **frozen**.
- Do **not** change these interfaces without team discussion.
- This ensures all agents remain compatible as new algorithms are added.

---

### 7. Scripts vs Core Code
- Code under `scripts/` is for **experiments, benchmarking, and evaluation**.
- Core game logic must live under `gomoku/` or `agents/`.
- Core code should not depend on `scripts/`.


## License

MIT (see `LICENSE`).