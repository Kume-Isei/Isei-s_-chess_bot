"""Name: Isei Okhakume Paul
Project: Chess Bot
"""

import sys
import argparse
import threading
import chess
import chess.polyglot
import pygame

from chess_bot import Engine

# --------------------------------------------------------------------------
# Layout / theme
# --------------------------------------------------------------------------

SQUARE_SIZE = 80
BOARD_SIZE = SQUARE_SIZE * 8
SIDEBAR_WIDTH = 260
WINDOW_WIDTH = BOARD_SIZE + SIDEBAR_WIDTH
WINDOW_HEIGHT = BOARD_SIZE

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (246, 246, 105)
LEGAL_DOT = (100, 100, 100)
LAST_MOVE = (205, 210, 106)
CHECK_COLOR = (220, 90, 90)
SIDEBAR_BG = (35, 35, 40)
TEXT_COLOR = (230, 230, 230)
ACCENT = (120, 170, 230)

PIECE_UNICODE = {
    (chess.PAWN, chess.WHITE): "\u2659",
    (chess.KNIGHT, chess.WHITE): "\u2658",
    (chess.BISHOP, chess.WHITE): "\u2657",
    (chess.ROOK, chess.WHITE): "\u2656",
    (chess.QUEEN, chess.WHITE): "\u2655",
    (chess.KING, chess.WHITE): "\u2654",
    (chess.PAWN, chess.BLACK): "\u265F",
    (chess.KNIGHT, chess.BLACK): "\u265E",
    (chess.BISHOP, chess.BLACK): "\u265D",
    (chess.ROOK, chess.BLACK): "\u265C",
    (chess.QUEEN, chess.BLACK): "\u265B",
    (chess.KING, chess.BLACK): "\u265A",
}


class ChessGUI:
    def __init__(self, human_color=chess.WHITE, engine_time=3.0):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chess vs PyNegamaxBot")
        self.clock = pygame.time.Clock()

        self.piece_font = pygame.font.SysFont("segoeuisymbol,dejavusans,arial", 56)
        self.ui_font = pygame.font.SysFont("arial", 20)
        self.ui_font_bold = pygame.font.SysFont("arial", 24, bold=True)

        self.board = chess.Board()
        self.engine = Engine()
        self.human_color = human_color
        self.engine_time = engine_time

        self.selected_square = None
        self.legal_targets = []
        self.last_move = None
        self.status_text = "Your move" if human_color == chess.WHITE else "Engine thinking..."
        self.thinking = False
        self.engine_move_result = None
        self.game_over_text = None

        if self.board.turn != self.human_color:
            self._start_engine_move()

    # ---------------------------------------------------------------
    # Board <-> screen coordinate helpers
    # ---------------------------------------------------------------

    def square_to_screen(self, square):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        if self.human_color == chess.WHITE:
            x = file * SQUARE_SIZE
            y = (7 - rank) * SQUARE_SIZE
        else:
            x = (7 - file) * SQUARE_SIZE
            y = rank * SQUARE_SIZE
        return x, y

    def screen_to_square(self, pos):
        x, y = pos
        if x >= BOARD_SIZE:
            return None
        file = x // SQUARE_SIZE
        rank = y // SQUARE_SIZE
        if self.human_color == chess.WHITE:
            file = file
            rank = 7 - rank
        else:
            file = 7 - file
            rank = rank
        if 0 <= file <= 7 and 0 <= rank <= 7:
            return chess.square(file, rank)
        return None

    # ---------------------------------------------------------------
    # Engine move (threaded so the UI doesn't freeze)
    # ---------------------------------------------------------------

    def _start_engine_move(self):
        self.thinking = True
        self.status_text = "Engine thinking..."

        def run():
            move, score = self.engine.search(self.board, time_limit=self.engine_time)
            self.engine_move_result = (move, score)

        threading.Thread(target=run, daemon=True).start()

    def _apply_engine_move_if_ready(self):
        if self.engine_move_result is not None:
            move, score = self.engine_move_result
            self.engine_move_result = None
            self.thinking = False
            if move is not None:
                self.last_move = move
                self.board.push(move)
            self._update_status(score)

    def _update_status(self, engine_score=None):
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            self.status_text = f"Checkmate — {winner} wins"
        elif self.board.is_stalemate():
            self.status_text = "Stalemate — draw"
        elif self.board.is_insufficient_material():
            self.status_text = "Draw — insufficient material"
        elif self.board.can_claim_draw():
            self.status_text = "Draw available"
        elif self.board.is_check():
            self.status_text = "Check!"
        else:
            self.status_text = "Your move" if self.board.turn == self.human_color else "Engine thinking..."

        if engine_score is not None and self.board.turn == self.human_color:
            sign = "+" if engine_score >= 0 else ""
            self.status_text += f"   (eval {sign}{engine_score/100:.2f})"

    # ---------------------------------------------------------------
    # Input handling
    # ---------------------------------------------------------------

    def handle_click(self, pos):
        if self.board.is_game_over() or self.thinking or self.board.turn != self.human_color:
            return

        square = self.screen_to_square(pos)
        if square is None:
            return

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece is not None and piece.color == self.human_color:
                self.selected_square = square
                self.legal_targets = [
                    m.to_square for m in self.board.legal_moves if m.from_square == square
                ]
        else:
            if square == self.selected_square:
                self.selected_square = None
                self.legal_targets = []
                return

            move = chess.Move(self.selected_square, square)
            # handle promotion (always promote to queen for simplicity)
            piece = self.board.piece_at(self.selected_square)
            if piece and piece.piece_type == chess.PAWN and chess.square_rank(square) in (0, 7):
                move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

            if move in self.board.legal_moves:
                self.last_move = move
                self.board.push(move)
                self.selected_square = None
                self.legal_targets = []
                self._update_status()
                if not self.board.is_game_over():
                    self._start_engine_move()
            else:
                # maybe selecting a different own piece
                new_piece = self.board.piece_at(square)
                if new_piece is not None and new_piece.color == self.human_color:
                    self.selected_square = square
                    self.legal_targets = [
                        m.to_square for m in self.board.legal_moves if m.from_square == square
                    ]
                else:
                    self.selected_square = None
                    self.legal_targets = []

    # ---------------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------------

    def draw_board(self):
        for square in chess.SQUARES:
            x, y = self.square_to_screen(square)
            file, rank = chess.square_file(square), chess.square_rank(square)
            color = LIGHT_SQUARE if (file + rank) % 2 == 0 else DARK_SQUARE

            if self.last_move and square in (self.last_move.from_square, self.last_move.to_square):
                color = LAST_MOVE
            if square == self.selected_square:
                color = HIGHLIGHT

            pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

            if self.board.is_check():
                king_square = self.board.king(self.board.turn)
                if square == king_square:
                    pygame.draw.rect(self.screen, CHECK_COLOR, (x, y, SQUARE_SIZE, SQUARE_SIZE), 5)

        for square in self.legal_targets:
            x, y = self.square_to_screen(square)
            center = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
            if self.board.piece_at(square) is not None:
                pygame.draw.circle(self.screen, LEGAL_DOT, center, SQUARE_SIZE // 2 - 4, 4)
            else:
                pygame.draw.circle(self.screen, LEGAL_DOT, center, 10)

    def draw_pieces(self):
        for square, piece in self.board.piece_map().items():
            x, y = self.square_to_screen(square)
            symbol = PIECE_UNICODE[(piece.piece_type, piece.color)]
            fill = (255, 255, 255) if piece.color == chess.WHITE else (20, 20, 20)
            outline = (20, 20, 20) if piece.color == chess.WHITE else (255, 255, 255)

            # simple outline effect for visibility on both square colors
            text_surface = self.piece_font.render(symbol, True, outline)
            rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2 + 1, y + SQUARE_SIZE // 2 + 1))
            self.screen.blit(text_surface, rect)

            text_surface = self.piece_font.render(symbol, True, fill)
            rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
            self.screen.blit(text_surface, rect)

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, SIDEBAR_BG, (BOARD_SIZE, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT))

        title = self.ui_font_bold.render("PyNegamaxBot", True, ACCENT)
        self.screen.blit(title, (BOARD_SIZE + 20, 20))

        turn_str = "White to move" if self.board.turn == chess.WHITE else "Black to move"
        turn_surf = self.ui_font.render(turn_str, True, TEXT_COLOR)
        self.screen.blit(turn_surf, (BOARD_SIZE + 20, 60))

        # wrap status text
        words = self.status_text.split(" ")
        lines, current = [], ""
        for w in words:
            test = (current + " " + w).strip()
            if self.ui_font.size(test)[0] > SIDEBAR_WIDTH - 40:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)

        y = 100
        for line in lines:
            surf = self.ui_font.render(line, True, (255, 220, 120) if self.thinking else TEXT_COLOR)
            self.screen.blit(surf, (BOARD_SIZE + 20, y))
            y += 26

        # move history
        y += 20
        hist_title = self.ui_font.render("Moves:", True, ACCENT)
        self.screen.blit(hist_title, (BOARD_SIZE + 20, y))
        y += 28

        temp_board = chess.Board()
        move_lines = []
        for i, move in enumerate(self.board.move_stack):
            san = temp_board.san(move)
            temp_board.push(move)
            if i % 2 == 0:
                move_lines.append(f"{i // 2 + 1}. {san}")
            else:
                move_lines[-1] += f"   {san}"

        for line in move_lines[-12:]:
            surf = self.ui_font.render(line, True, TEXT_COLOR)
            self.screen.blit(surf, (BOARD_SIZE + 20, y))
            y += 24

        hint = self.ui_font.render("Press R to restart", True, (150, 150, 150))
        self.screen.blit(hint, (BOARD_SIZE + 20, WINDOW_HEIGHT - 30))

    def restart(self):
        self.board = chess.Board()
        self.engine = Engine()
        self.selected_square = None
        self.legal_targets = []
        self.last_move = None
        self.engine_move_result = None
        self.thinking = False
        self.status_text = "Your move" if self.human_color == chess.WHITE else "Engine thinking..."
        if self.board.turn != self.human_color:
            self._start_engine_move()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.restart()

            if self.thinking:
                self._apply_engine_move_if_ready()

            self.screen.fill((0, 0, 0))
            self.draw_board()
            self.draw_pieces()
            self.draw_sidebar()
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Graphical chess GUI for the negamax engine.")
    parser.add_argument("--time", type=float, default=3.0, help="Engine thinking time per move (seconds)")
    parser.add_argument("--flip", action="store_true", help="Play as Black instead of White")
    args = parser.parse_args()

    human_color = chess.BLACK if args.flip else chess.WHITE
    gui = ChessGUI(human_color=human_color, engine_time=args.time)
    gui.run()
