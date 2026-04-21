import threading
import pygame

from engine import *

class GUI:
    running: bool
    
    cell_size: int
    disc_size: int
    
    board_background_color: pygame.color.Color
    board_grid_color: pygame.color.Color
    
    white_disc_color: pygame.color.Color
    black_disc_color: pygame.color.Color
    
    engine: Engine
    provider: InputProvider
    
    thread: threading.Thread
    
    screen: pygame.surface.Surface
    
    def __init__(self, engine: Engine, provider: InputProvider) -> None:
        self.running = False

        self.cell_size = 64
        self.disc_size = 48        
        
        self.white_disc_color = pygame.color.Color(244, 253, 250)
        self.black_disc_color = pygame.color.Color(19, 26, 24)
        self.board_background_color = pygame.color.Color(0, 144, 103)
        self.board_grid_color = pygame.color.Color(0, 72, 52)
        
        self.engine = engine
        self.provider = provider
        
    
    def run(self):
        self.init()
        
        self.running = True
        self.thread = threading.Thread(target=self.loop)
        
        self.thread.start()

        while self.running:
            for event in pygame.event.get():
                self.process(event)

            self.render()   
        
    def init(self):
        pygame.init()
        pygame.display.set_caption('Othello')
        self.screen = pygame.display.set_mode((1280, 720))
        
    def process(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.stop()
        # elif event.type == pygame.KEYDOWN:
        #     if event.key == pygame.K_SPACE:
        #         self.engine.tick()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                x, y = event.pos
                pos = Position(y // self.cell_size, x // self.cell_size)
                
                if self.provider.is_waiting_move():
                    for move in self.provider.game_state.moves: # type: ignore
                        if move.position == pos:
                            self.provider.answer_move(move)
                            break
    def loop(self):
        while self.running and not self.engine.game_state.is_over():
            self.engine.tick()
    
    def render(self):
        board = self.engine.game_state.board
        
        player = self.engine.game_state.player
        moves = self.engine.game_state.moves
        
        board_size = self.cell_size * board.size
        
        self.screen.fill((255, 255, 255))
        
        pygame.draw.rect(
            self.screen,
            self.board_background_color,
            (0, 0, board_size, board_size)
        )
        
        for i in range(board.size + 1):
            offset = i * self.cell_size

            pygame.draw.line(
                self.screen,
                self.board_grid_color,
                (0, offset),
                (board_size, offset)
            )

            pygame.draw.line(
                self.screen,
                self.board_grid_color,
                (offset, 0),
                (offset, board_size)
            )
            
        for row in range(board.size):
            for col in range(board.size):
                x = col * self.cell_size + self.cell_size // 2
                y = row * self.cell_size + self.cell_size // 2
                
                piece = board[row, col]
                
                if piece != None:
                    color = self.black_disc_color if piece == Player.BLACK else self.white_disc_color
                    
                    pygame.draw.circle(
                        self.screen,
                        color,
                        (x, y),
                        self.disc_size // 2,
                    )

        for move in moves:
            color = self.black_disc_color if player == Player.BLACK else self.white_disc_color
            
            x = move.position.col * self.cell_size + self.cell_size // 2
            y = move.position.row * self.cell_size + self.cell_size // 2
            
            pygame.draw.circle(
                self.screen,
                color,
                (x, y),
                self.disc_size // 2,
                2
            )
        
        pygame.display.flip()
            
    def stop(self):
        self.running = False
        
        if self.provider.is_waiting_move():
            self.provider.answer_move(self.provider.game_state.moves[0]) # type: ignore
    