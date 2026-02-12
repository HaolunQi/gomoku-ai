import os
import pygame as pg

from gomoku.game import Game
from gomoku.board import Board, BLACK, WHITE, EMPTY, BOARD_SIZE


class PygameUI:
    def __init__(self):
        # Configure window and layout
        self.width = 615
        self.height = 615
        self.grid_origin = 27
        self.cell = 40
        self.asset_dir = os.path.join(os.path.dirname(__file__), "assets")

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
        # Convert board cell (x, y) to pixel coordinates
        x, y = move
        return (self.grid_origin + x * self.cell, self.grid_origin + y * self.cell)

    def pixel_to_cell(self, pos):
        # Convert pixel coordinates to nearest board cell, or None if out of bounds
        px, py = pos
        min_p = self.grid_origin - self.cell / 2
        max_p = self.grid_origin + (BOARD_SIZE - 1) * self.cell + self.cell / 2
        if not (min_p <= px <= max_p and min_p <= py <= max_p):
            return None
        x = int((px - self.grid_origin) / self.cell + 0.5)
        y = int((py - self.grid_origin) / self.cell + 0.5)
        return (x, y)

    def _is_ai_turn(self, game):
        # Return True if the current side is controlled by an agent
        return game.agent_for_turn() is not None

    def _maybe_ai_move_with_delay(self, game, now_ms, w):
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
        if self._is_ai_turn(game):
            return

        x, y = self.hover
        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            return
        if game.board.grid[x][y] != EMPTY:
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

    def _restart(self, old):
        # Restart with a fresh board but keep the same agents
        return Game(
            board=Board(),
            black_agent=old.black_agent,
            white_agent=old.white_agent,
        )

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

                elif event.type == pg.MOUSEBUTTONDOWN and not w and not self._is_ai_turn(game):
                    if event.button != 1:
                        continue
                    move = self.pixel_to_cell(pg.mouse.get_pos())
                    if move is not None:
                        game.step(move)
                        self._ai_waiting = False

            clock.tick(60)
            pg.display.update()

        pg.quit()
