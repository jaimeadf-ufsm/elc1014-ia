import threading
import pygame

from agent import *
from match import *
from game import *
from move import *
from player import *
from position import *
from provider import *

# Interface gráfica (Pygame) para visualizar e conduzir uma partida.
#
# A GUI renderiza o tabuleiro 6x6, as peças, as jogadas legais e uma
# pré-visualização de capturas ao passar o mouse. Também exibe um painel lateral
# com placar, jogador da vez e feedback de "Thinking" enquanto um agente decide.
#
# Ela se integra com:
#   - Match, para avançar a partida e acessar histórico/métricas;
#   - InputProvider, para receber jogadas humanas quando um HumanAgent está ativo.
#
# Para manter o loop de eventos e renderização responsivo, a execução de um turno
# (matchup.turn) ocorre em uma thread de trabalho quando necessário.
class GUI:
    matchup: Match
    provider: InputProvider
    
    mode: str
    
    running: bool
    
    width: int
    height: int
    
    fps: int
    
    board_margin: int
    panel_width: int
    
    cell_size: int
    disc_radius: int
    spinner_radius: int
    
    palette: dict[str, pygame.color.Color]
    
    screen: pygame.surface.Surface
    clock: pygame.time.Clock
    
    font_small: pygame.font.Font
    font_medium: pygame.font.Font
    font_large: pygame.font.Font
    
    board_rect: pygame.Rect
    panel_rect: pygame.Rect
    
    hovered_move: Move | None
    spinner_phase: float
    
    def __init__(
        self,
        engine: Match,
        provider: InputProvider,
        mode: str
    ) -> None:
        self.matchup = engine
        self.provider = provider
        self.mode = mode
        
        self.running = False
        
        self.width = 980
        self.height = 720
        
        self.fps = 60
        
        self.board_margin = 24
        self.panel_width = 284
        
        self.cell_size = 0
        self.disc_radius = 0
        self.spinner_radius = 13
        
        self.palette = {
            'bg': pygame.color.Color(232, 239, 229),
            'panel': pygame.color.Color(249, 252, 247),
            'board': pygame.color.Color(30, 123, 82),
            'grid': pygame.color.Color(22, 88, 58),
            'black': pygame.color.Color(24, 24, 26),
            'white': pygame.color.Color(244, 244, 242),
            'legal': pygame.color.Color(255, 250, 235),
            'hover': pygame.color.Color(245, 216, 90),
            'flip': pygame.color.Color(244, 140, 98),
            'text': pygame.color.Color(42, 52, 46),
            'muted': pygame.color.Color(108, 122, 111),
            'winner': pygame.color.Color(232, 96, 51),
            'shadow': pygame.color.Color(0, 0, 0, 36),
        }

        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)

        self.hovered_move= None
        self.spinner_phase = 0.0

        self.worker_thread= None
        self.worker_pending = False

    def run(self):
        self._init()
        self.running = True

        while self.running:
            for event in pygame.event.get():
                self._process(event)

            self._update()
            self._render()
            self.clock.tick(self.fps)

        self._shutdown()

    def _init(self):
        pygame.init()
        pygame.display.set_caption('Othello')
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        
        self.font_small = pygame.font.SysFont('verdana', 20)
        self.font_medium = pygame.font.SysFont('verdana', 26)
        self.font_large = pygame.font.SysFont('verdana', 34, bold=True)

        board_side = min(
            self.height - 2 * self.board_margin,
            self.width - self.panel_width - 2 * self.board_margin,
        )
        
        self.board_rect = pygame.Rect(
            self.board_margin,
            self.board_margin,
            board_side,
            board_side,
        )
        
        self.panel_rect = pygame.Rect(
            self.board_rect.right + 18,
            self.board_rect.top,
            self.panel_width - 24,
            self.board_rect.height
        )

        self.cell_size = self.board_rect.width // self.matchup.state.board.size
        self.disc_radius = max(8, int(self.cell_size * 0.36))

    def _process(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._restart_game()
            elif event.key == pygame.K_SPACE:
                self._start_turn_worker()
        elif event.type == pygame.MOUSEMOTION:
            x, y = event.pos

            col = (x - self.board_rect.left) // self.cell_size
            row = (y - self.board_rect.top) // self.cell_size

            target = Position(row, col)
            
            self.hovered_move = None
            
            for move in self.matchup.state.moves:
                if move.position == target:
                    self.hovered_move = move
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode != 'auto':
                self._start_turn_worker()

            if self.provider.is_waiting_move() and self.hovered_move is not None:
                self.provider.answer_move(self.hovered_move)

    def _update(self):
        self.spinner_phase = (self.spinner_phase + 0.15) % (2 * 3.1415926535)

        if self.mode == 'auto':
            self._start_turn_worker()
            
        if isinstance(self.matchup.get_player_agent(self.matchup.state.player), HumanAgent):
            self._start_turn_worker()
            
    def _shutdown(self):
        self.running = False
        self._stop_turn_worker()
        
        pygame.quit()

    def _render(self):
        self.screen.fill(self.palette['bg'])
        
        self._render_board()
        self._render_discs()
        self._render_moves()
        self._render_preview()
        self._render_side_panel()
        
        pygame.display.flip()

    def _render_board(self):
        pygame.draw.rect(self.screen, self.palette['board'], self.board_rect)

        for i in range(self.matchup.state.board.size + 1):
            offset = i * self.cell_size
            
            pygame.draw.line(
                self.screen,
                self.palette['grid'],
                (self.board_rect.left, self.board_rect.top + offset),
                (self.board_rect.right, self.board_rect.top + offset),
                2,
            )
            
            pygame.draw.line(
                self.screen,
                self.palette['grid'],
                (self.board_rect.left + offset, self.board_rect.top),
                (self.board_rect.left + offset, self.board_rect.bottom),
                2,
            )

    def _render_discs(self):
        board = self.matchup.state.board

        for row in range(board.size):
            for col in range(board.size):
                piece = board[row, col]
                
                if piece is None:
                    continue

                cx, cy = self._compute_cell_center(row, col)
                color = self._get_player_color(piece)
                shadow_pos = (cx + 2, cy + 3)

                pygame.draw.circle(self.screen, self.palette['shadow'], shadow_pos, self.disc_radius)
                pygame.draw.circle(self.screen, color, (cx, cy), self.disc_radius)

    def _render_moves(self):
        state = self.matchup.state
        active_color = self._get_player_color(state.player)

        for move in state.moves:
            cx, cy = self._compute_cell_center(move.position.row, move.position.col)
            radius = max(5, self.disc_radius // 3)

            pygame.draw.circle(self.screen, self.palette['legal'], (cx, cy), radius + 3)
            pygame.draw.circle(self.screen, active_color, (cx, cy), radius)

    def _render_preview(self):
        if self.hovered_move is None:
            return

        hover_cell = self._compute_cell_rect(self.hovered_move.position.row, self.hovered_move.position.col)
        pygame.draw.rect(self.screen, self.palette['hover'], hover_cell, width=4, border_radius=4)

        for capture in self.hovered_move.captures:
            cell = self._compute_cell_rect(capture.row, capture.col)
            pygame.draw.rect(self.screen, self.palette['flip'], cell.inflate(-8, -8), width=3, border_radius=6)

    def _render_side_panel(self):
        state = self.matchup.state
        
        pygame.draw.rect(self.screen, self.palette['panel'], self.panel_rect, border_radius=12)

        black_pieces = state.board.count_pieces(Player.BLACK)
        white_pieces = state.board.count_pieces(Player.WHITE)

        y = self.panel_rect.top + 24
        y = self._draw_text('Turn', self.font_small, self.palette['muted'], self.panel_rect.left + 18, y)

        if state.is_over():
            turn_text = 'Finished'
        else:
            turn_text = 'Black' if state.player == Player.BLACK else 'White'
            
        y = self._draw_text(turn_text, self.font_large, self.palette['text'], self.panel_rect.left + 18, y + 2)

        y += 16
        y = self._draw_text('Black', self.font_small, self.palette['muted'], self.panel_rect.left + 18, y)
        y = self._draw_text(str(black_pieces), self.font_medium, self.palette['text'], self.panel_rect.left + 18, y)

        y += 12
        y = self._draw_text('White', self.font_small, self.palette['muted'], self.panel_rect.left + 18, y)
        y = self._draw_text(str(white_pieces), self.font_medium, self.palette['text'], self.panel_rect.left + 18, y)

        y += 18
        if state.is_over():
            winner_text = 'Draw'
            
            if state.winner == Player.BLACK:
                winner_text = 'Black Wins'
            elif state.winner == Player.WHITE:
                winner_text = 'White Wins'
            
            y = self._draw_text(winner_text, self.font_medium, self.palette['winner'], self.panel_rect.left + 18, y)

        y = self.panel_rect.bottom - 108
        
        elapsed = self.matchup.history[-1].metrics.get('elapsed_time')
        
        if self.worker_pending and not self.provider.is_waiting_move():
            y = self._draw_text('Thinking', self.font_small, self.palette['muted'], self.panel_rect.left + 18, y)
            self._draw_spinner(self.panel_rect.left + 120, y - 10)
        elif elapsed is not None:
                y = self._draw_text(f'Thought for {elapsed:.2f}s', self.font_small, self.palette['muted'], self.panel_rect.left + 18, y)

        if self.mode != 'auto':
            self._draw_text('<Space>: Step', self.font_small, self.palette['muted'], self.panel_rect.left + 18, self.panel_rect.bottom - 72)

        self._draw_text('<R>: Restart', self.font_small, self.palette['muted'], self.panel_rect.left + 18, self.panel_rect.bottom - 40)

    def _draw_spinner(self, cx: int, cy: int):
        for i in range(8):
            angle = self.spinner_phase + i * (3.1415926535 / 4.0)
            
            x = int(cx + self.spinner_radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x)
            y = int(cy + self.spinner_radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y)
            
            strength = (i + 1) / 8.0
            
            color = pygame.color.Color(
                int(self.palette['text'].r * strength),
                int(self.palette['text'].g * strength),
                int(self.palette['text'].b * strength),
            
            )
            pygame.draw.circle(self.screen, color, (x, y), 3)

    def _draw_text(self, text: str, font: pygame.font.Font, color: pygame.color.Color, x: int, y: int):
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))
        
        return y + surface.get_height()

    def _compute_cell_center(self, row: int, col: int):
        x = self.board_rect.left + col * self.cell_size + self.cell_size // 2
        y = self.board_rect.top + row * self.cell_size + self.cell_size // 2
        
        return x, y

    def _compute_cell_rect(self, row: int, col: int):
        return pygame.Rect(
            self.board_rect.left + col * self.cell_size,
            self.board_rect.top + row * self.cell_size,
            self.cell_size,
            self.cell_size,
        )
        
    def _restart_game(self):
        self._stop_turn_worker()
        self.matchup.restart()
    
    def _start_turn_worker(self):
        if self.worker_pending:
            return
        
        if self.matchup.state.is_over():
            return
        
        def worker():
            self.matchup.turn()
            self.worker_pending = False

        self.worker_pending = True

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
    
    def _stop_turn_worker(self):
        if self.provider.is_waiting_move():
            self.provider.answer_move(None)
        
    def _get_player_color(self, player: Player):
        return self.palette['black'] if player == Player.BLACK else self.palette['white']
