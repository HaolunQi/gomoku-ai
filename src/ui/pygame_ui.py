import os
import pygame as pg

from gomoku.game import Game
from gomoku.board import Board, BLACK, WHITE, EMPTY, BOARD_SIZE
from heuristics.evaluate import debug_evaluate, debug_order_moves


class PygameUI:
    def __init__(self):
        # Configure window and layout
        self.width = 615
        self.height = 615
        self.grid_origin = 27
        self.cell = 40
        self.asset_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.history = []
        self.force_mode = False

        # Track hovered cell for preview rendering
        self.hover = None

        # Non-blocking AI delay state
        self.ai_delay_ms = 300
        self._ai_waiting = False
        self._ai_wait_start_ms = 0

    def load(self, name):
        # Load an image asset with alpha
        return pg.image.load(os.path.join(self.asset_dir, name)).convert_alpha()

    def cell_to_pixel(self, move):
        # Convert board cell (r, c) to pixel coordinates
        r, c = move
        x = self.grid_origin + c * self.cell
        y = self.grid_origin + r * self.cell
        return (x, y)

    def pixel_to_cell(self, pos):
        # Convert pixel coordinates to nearest board cell (r, c), or None if out of bounds
        px, py = pos
        min_p = self.grid_origin - self.cell / 2
        max_p = self.grid_origin + (BOARD_SIZE - 1) * self.cell + self.cell / 2
        if not (min_p <= px <= max_p and min_p <= py <= max_p):
            return None

        c = int((px - self.grid_origin) / self.cell + 0.5)
        r = int((py - self.grid_origin) / self.cell + 0.5)
        return (r, c)

    def _is_ai_turn(self, game):
        # Return True if the current side is controlled by an agent
        return game.agent_for_turn() is not None

    def _maybe_ai_move_with_delay(self, game, now_ms, w):
        # If paused, never let AI move
        if self.paused:
            self._ai_waiting = False
            return

        # If it's AI's turn, wait ai_delay_ms then apply the AI move (non-blocking)
        if w is not None:
            self._ai_waiting = False
            return

        if not self._is_ai_turn(game):
            self._ai_waiting = False
            return

        if not self._ai_waiting:
            self._ai_waiting = True
            self._ai_wait_start_ms = now_ms
            return

        if now_ms - self._ai_wait_start_ms >= self.ai_delay_ms:
            self._ai_waiting = False
            self._push_history(game)
            game.maybe_ai_move()

    def _draw_pieces(self, screen, game, black_img, white_img):
        # Draw all placed stones
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                s = game.board.grid[row][col]
                if s == BLACK:
                    rect = black_img.get_rect(center=self.cell_to_pixel((row, col)))
                    screen.blit(black_img, rect)
                elif s == WHITE:
                    rect = white_img.get_rect(center=self.cell_to_pixel((row, col)))
                    screen.blit(white_img, rect)

    def _draw_hover_preview(self, screen, game, black_img, white_img, w):
        # Draw a translucent preview stone under the mouse for human turns
        if w or self.hover is None:
            return
        if self.paused:
            return
        if self._is_ai_turn(game):
            return

        r, c = self.hover
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            return
        if game.board.grid[r][c] != EMPTY:
            return

        img = black_img if game.to_move == BLACK else white_img
        preview = img.copy()
        preview.set_alpha(120)
        rect = preview.get_rect(center=self.cell_to_pixel(self.hover))
        screen.blit(preview, rect)

    def _draw_win_overlay(self, screen, font_big, font_small, w):
        # Draw end-of-game overlay and restart hint
        if not w:
            return

        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((255, 255, 255, 170))
        screen.blit(overlay, (0, 0))

        msg = "BLACK WINS!" if w == BLACK else "WHITE WINS!"
        text = font_big.render(msg, True, (0, 0, 0))
        screen.blit(text, text.get_rect(center=(self.width // 2, self.height // 2 - 20)))

        hint = "Press R to restart (Esc to quit)"
        text2 = font_small.render(hint, True, (0, 0, 0))
        screen.blit(text2, text2.get_rect(center=(self.width // 2, self.height // 2 + 35)))

    def _draw_pause_overlay(self, screen, font_big, font_small, w):
        # Draw pause overlay
        if not self.paused or w:
            return

        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        text = font_big.render("PAUSED", True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=(self.width // 2, self.height // 2 - 20)))

        hint = "Press Space to resume"
        text2 = font_small.render(hint, True, (255, 255, 255))
        screen.blit(text2, text2.get_rect(center=(self.width // 2, self.height // 2 + 35)))

    def _restart(self, old):
        # Restart with a fresh board but keep the same agents
        return Game(
            board=Board(),
            black_agent=old.black_agent,
            white_agent=old.white_agent,
        )

    def _push_history(self, game):
        # Save current game state for undo
        self.history.append({
            "board": game.board.copy(),
            "to_move": game.to_move,
        })

    def _undo(self, game):
        # Restore previous game state from history stack
        if not self.history:
            print("No history to undo.")
            return game

        state = self.history.pop()
        game.board = state["board"]
        game.to_move = state["to_move"]

        # Reset AI delay state after undo
        self._ai_waiting = False
        self._ai_wait_start_ms = 0
        return game

    def _step_ai_once(self, game):
        # Execute exactly one AI move (used in paused/debug mode)
        if game.winner() is not None:
            print("Game is over.")
            return

        if not self._is_ai_turn(game):
            print("Current turn is not AI.")
            return

        # Save state before applying AI move
        self._push_history(game)
        game.maybe_ai_move()
        print("AI stepped forward once.")
        print(game.board)

    def _force_place(self, game, move):
        # Force a move on the board
        if move is None:
            print("Invalid move: None")
            return

        r, c = move
        if not (0 <= r < game.board.size and 0 <= c < game.board.size):
            print("Out of bounds:", move)
            return

        if game.board.grid[r][c] != EMPTY:
            print("Cell is not empty:", move)
            return

        self._push_history(game)
        game.board.place(move, game.to_move)
        game.to_move = WHITE if game.to_move == BLACK else BLACK

        self._ai_waiting = False
        self._ai_wait_start_ms = 0

        print(f"\n[FORCE PLACE] move={move}")
        print(game.board)
        debug_evaluate(game.board, game.to_move)
        moves = game.board.candidate_moves()
        debug_order_moves(game.board, moves, game.to_move, top_k=10)

    def run(self, game):
        # Main pygame loop
        pg.init()
        screen = pg.display.set_mode((self.width, self.height))
        clock = pg.time.Clock()

        bg = self.load("bg.png")
        black_img = self.load("storn_black.png")
        white_img = self.load("storn_white.png")
        font_big = pg.font.Font(os.path.join(self.asset_dir, "font.ttf"), 48)
        font_small = pg.font.Font(os.path.join(self.asset_dir, "font.ttf"), 22)

        pg.display.set_caption("Gomoku")

        running = True
        while running:
            now_ms = pg.time.get_ticks()

            screen.blit(bg, (0, 0))
            self.hover = self.pixel_to_cell(pg.mouse.get_pos())
            w = game.winner()

            self._maybe_ai_move_with_delay(game, now_ms, w)
            w = game.winner()

            # Draw
            self._draw_pieces(screen, game, black_img, white_img)
            self._draw_hover_preview(screen, game, black_img, white_img, w)
            self._draw_pause_overlay(screen, font_big, font_small, w)
            self._draw_win_overlay(screen, font_big, font_small, w)

            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False

                    elif event.key == pg.K_r:
                        game = self._restart(game)
                        self.hover = None
                        self._ai_waiting = False
                        self._ai_wait_start_ms = 0
                        self.paused = False
                    elif event.key == pg.K_SPACE and not w:
                        self.paused = not self.paused
                        self._ai_waiting = False
                        self._ai_wait_start_ms = now_ms

                        if self.paused:
                            print("\nPaused. Current board:")
                            print(game.board)
                            print("Next to move:", game.to_move)
                            debug_evaluate(game.board, game.to_move)
                            moves = game.board.candidate_moves()
                            debug_order_moves(game.board, moves, game.to_move, top_k=10)

                    elif event.key == pg.K_RIGHT and self.paused and not w:
                        self._step_ai_once(game)
                        print("\nForward. Current board:")
                        print(game.board)
                        moves = game.board.candidate_moves()
                        debug_evaluate(game.board, game.to_move)
                        debug_order_moves(game.board, moves, game.to_move, top_k=10)

                    elif event.key == pg.K_LEFT and self.paused:
                        game = self._undo(game)
                        print("\nBack. Current board:")
                        print(game.board)
                        moves = game.board.candidate_moves()
                        debug_evaluate(game.board, game.to_move)
                        debug_order_moves(game.board, moves, game.to_move, top_k=10)

                    elif event.key == pg.K_f and self.paused:
                        self.force_mode = not self.force_mode
                        print("Force mode:", self.force_mode)

                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button != 1:
                        continue

                    move = self.pixel_to_cell(pg.mouse.get_pos())

                    if self.paused and self.force_mode:
                        self._force_place(game, move)

                    elif not w and not self.paused and not self._is_ai_turn(game):
                        if move is not None:
                            self._push_history(game)
                            game.step(move)
                            self._ai_waiting = False

            clock.tick(60)
            pg.display.update()

        pg.quit()