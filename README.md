# gomoku-ai

Gomoku (15x15, five-in-a-row) with a clean separation between **game logic**, **agents**, and **pygame UI**.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
```

### Pygame UI (human via mouse; agents optional)

```bash
python src/main.py
```

> In pygame mode, **mouse clicks** provide human moves. `HumanAgent` (CLI-based) is **not** used in pygame because it calls `input()`.

### CLI / scripts (agent vs agent, or CLI human)

```bash
python scripts/run_match.py --black random --white greedy
python scripts/run_match.py --black human --white greedy
python scripts/benchmark.py --black greedy --white random --games 200 --seed 0
```

## Project structure

- `src/gomoku/`: board + rules + game controller (UI-independent)
- `src/agents/`: agent implementations (Random / Greedy / Human CLI)
- `src/ui/`: pygame UI
- `tests/`: pytest tests (including smoke tests for agents)
- `scripts/`: match runner + benchmark tooling

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

### 6. CI Dependencies
- CI installs a **minimal dependency set** via `requirements-ci.txt`.
- UI-related dependencies (e.g. `pygame`) are excluded from CI on purpose.

---

### 7. Frozen Core APIs
- The public APIs of `Board` and `Agent` are considered **frozen**.
- Do **not** change these interfaces without team discussion.
- This ensures all agents remain compatible as new algorithms are added.

---

### 8. Scripts vs Core Code
- Code under `scripts/` is for **experiments, benchmarking, and evaluation**.
- Core game logic must live under `gomoku/` or `agents/`.
- Core code should not depend on `scripts/`.


## License

MIT (see `LICENSE`).