"""
Minimal Flask API for Gomoku vs AlphaBetaAgent.
Expects repo layout: gomoku-ai/web/ (this file) and gomoku-ai/src/ (engine).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Resolve engine package root (sibling of web/)
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from flask import Flask, jsonify, render_template, request

from agents.ab_agent import AlphaBetaAgent
from gomoku.board import BLACK, BOARD_SIZE, EMPTY, WHITE, Board
from gomoku.game import Game

app = Flask(__name__, template_folder="templates", static_folder="static")

_ai = AlphaBetaAgent()


def _normalize_cell(v):
    if v is None or v == "":
        return EMPTY
    if v == BLACK or v == WHITE:
        return v
    if isinstance(v, str) and len(v) == 1 and v.strip() == "":
        return EMPTY
    return v


def board_from_grid(grid) -> Board:
    if not grid or len(grid) != BOARD_SIZE:
        raise ValueError(f"grid must be {BOARD_SIZE}x{BOARD_SIZE}")
    b = Board(BOARD_SIZE)
    for r in range(BOARD_SIZE):
        row = grid[r]
        if not row or len(row) != BOARD_SIZE:
            raise ValueError(f"grid must be {BOARD_SIZE}x{BOARD_SIZE}")
        for c in range(BOARD_SIZE):
            stone = _normalize_cell(row[c])
            if stone not in (EMPTY, BLACK, WHITE):
                raise ValueError("invalid cell value")
            b._grid[r][c] = stone
    return b


def infer_to_move(board: Board) -> str:
    black_n = sum(row.count(BLACK) for row in board._grid)
    white_n = sum(row.count(WHITE) for row in board._grid)
    if black_n == white_n:
        return BLACK
    if black_n == white_n + 1:
        return WHITE
    raise ValueError("illegal stone counts for Gomoku")


def grid_from_board(board: Board):
    return [list(row) for row in board.grid]


def make_game(board: Board, human_side: str, to_move: str) -> Game:
    human_side = (human_side or "black").lower()
    if human_side == "black":
        return Game(board, black_agent=None, white_agent=_ai, to_move=to_move)
    if human_side == "white":
        return Game(board, black_agent=_ai, white_agent=None, to_move=to_move)
    raise ValueError("human_side must be 'black' or 'white'")


def state_payload(game: Game):
    w = game.winner()
    over = game.is_over()
    return {
        "grid": grid_from_board(game.board),
        "to_move": game.to_move,
        "winner": w,
        "game_over": over,
        "is_draw": over and w is None,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/new")
def api_new():
    side = (request.args.get("side") or "black").lower()
    try:
        board = Board(BOARD_SIZE)
        game = make_game(board, side, BLACK)
        if side == "white":
            if not game.maybe_ai_move():
                return jsonify({"error": "failed to apply AI opening move"}), 500
        return jsonify(state_payload(game))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/move")
def api_move():
    data = request.get_json(silent=True) or {}
    grid = data.get("grid")
    human_side = (data.get("human_side") or "black").lower()
    move = data.get("move")
    client_to_move = data.get("to_move")

    if not isinstance(move, (list, tuple)) or len(move) != 2:
        return jsonify({"error": "move must be [row, col]"}), 400

    try:
        r, c = int(move[0]), int(move[1])
    except (TypeError, ValueError):
        return jsonify({"error": "move must be integers"}), 400

    try:
        board = board_from_grid(grid)
        inferred = infer_to_move(board)
        if client_to_move is not None and client_to_move != inferred:
            return jsonify({"error": "to_move does not match board state"}), 400
        to_move = inferred
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    human_stone = BLACK if human_side == "black" else WHITE
    if human_side not in ("black", "white"):
        return jsonify({"error": "human_side must be 'black' or 'white'"}), 400

    if to_move != human_stone:
        return jsonify({"error": "not human's turn"}), 400

    game = make_game(board, human_side, to_move)

    if game.is_over():
        return jsonify({"error": "game is already over"}), 400

    if not board.in_bounds((r, c)) or not board.is_empty((r, c)):
        return jsonify({"error": "illegal move"}), 400

    if not game.step((r, c)):
        return jsonify({"error": "failed to apply move"}), 400

    if not game.is_over():
        if not game.maybe_ai_move():
            return jsonify({"error": "AI failed to move"}), 500

    return jsonify(state_payload(game))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
