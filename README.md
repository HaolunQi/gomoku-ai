# gomoku-ai

Gomoku (15x15, five-in-a-row) with a clean separation between **game logic**, **agents**, and **pygame UI**.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
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

## License

MIT (see `LICENSE`).
