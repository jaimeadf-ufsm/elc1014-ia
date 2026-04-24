from abc import abstractmethod
from typing import Tuple
from itertools import chain

from board import Player
from player import *
from board import *
from player import Player
from position import *
from move import *

class GameState:
    count: int

    board: Board
    
    player: Player
    moves: list[Move]

    winner: Player | None
    
    def __init__(self):
        self.count = 0
        self.board = Board(0)
        self.player = Player.BLACK
        self.moves = []
        self.winner = None
    
    def is_over(self):
        return len(self.moves) == 0

class GameVariant:
    @abstractmethod
    def create_game(self) -> GameState:
        pass
    
    @abstractmethod
    def continue_game(self, board: Board, player: Player) -> bool:
        pass
    
    @abstractmethod
    def make_move(self, state: GameState, move: Move) -> GameState:
        pass
    
class ClassicalGameVariant(GameVariant):
    size: int
    directions: list[Tuple[int, int]]
    
    def __init__(self, size: int = 6):
        self.size = size
        self.directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1) 
        ]
    
    def create_game(self):
        state = GameState()
        
        middle = self.size // 2 - 1
        
        state.count = 0

        state.board = Board(self.size)
        state.board = state.board.with_piece(middle, middle, Player.WHITE)
        state.board = state.board.with_piece(middle + 1, middle, Player.BLACK)
        state.board = state.board.with_piece(middle, middle  + 1, Player.BLACK)
        state.board = state.board.with_piece(middle + 1, middle + 1, Player.WHITE)
       
        state.player = Player.BLACK
        state.moves = self.get_legal_moves(state.board, state.player)
        
        state.winner = None
        
        return state

    def make_move(self, state: GameState, move: Move):
        new_state = GameState()
        
        player = state.player
        opponent = state.player.opponent()

        new_state.count = state.count + 1
        
        new_pieces = chain(move.captures, move.placements)
        new_state.board = state.board.with_pieces(new_pieces, player)
        
        new_state.player = opponent
        new_state.moves = self.get_legal_moves(new_state.board, opponent)
        
        if len(new_state.moves) == 0:
            new_state.player = player
            new_state.moves = self.get_legal_moves(new_state.board, player)
        
        if new_state.is_over():
            new_state.winner = self.get_winner(new_state.board)
        
        return new_state
        
    def get_legal_moves(self, board: Board, player: Player):
        moves: list[Move] = []
        opponent = player.opponent()
        
        for row in range(board.size):
            for col in range(board.size):
                move = Move()
                move.position = Position(row, col)
                move.captures = []
                move.placements = [Position(row, col)]
                
                if board[row, col] != None:
                    continue
                
                for dr, dc in self.directions:
                    dir_captures: list[Position] = []
                    
                    cur_row = row + dr
                    cur_col = col + dc
                    
                    # Caminha enquanto encontrar peças do oponente dentro do
                    # tabuleiro
                    while board[cur_row, cur_col] == opponent:
                        dir_captures.append(Position(cur_row, cur_col))
                        
                        cur_row += dr
                        cur_col += dc
                    
                    # Se o loop parou e encontrou uma peça do jogador atual,
                    # fechou o oponente
                    if board[cur_row, cur_col] != player:
                        continue
                    
                    move.captures.extend(dir_captures)
                
                if len(move.captures) != 0:
                    moves.append(move)
        
        return moves
                
    def get_winner(self, board: Board):
        black_pieces = board.count_pieces(Player.BLACK)
        white_pieces = board.count_pieces(Player.WHITE)
        
        if black_pieces > white_pieces:
            return Player.BLACK
        elif white_pieces > black_pieces:
            return Player.WHITE
        else:
            return None

class WrapAroundGameVariant(GameVariant):
    size: int
    directions: list[Tuple[int, int]]
    
    def __init__(self, size: int = 8):
        self.size = size
        self.directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1) 
        ]
    
    def create_game(self):
        state = GameState()
        
        middle = self.size // 2 - 1
        
        state.count = 0

        state.board = Board(self.size)
        state.board = state.board.with_piece(middle, middle, Player.WHITE)
        state.board = state.board.with_piece(middle + 1, middle, Player.BLACK)
        state.board = state.board.with_piece(middle, middle  + 1, Player.BLACK)
        state.board = state.board.with_piece(middle + 1, middle + 1, Player.WHITE)
       
        state.player = Player.BLACK
        state.moves = self.get_legal_moves(state.board, state.player)
        
        state.winner = None
        
        return state
    
    def make_move(self, state: GameState, move: Move):
        new_state = GameState()
        
        player = state.player
        opponent = state.player.opponent()
        
        new_state.count = state.count + 1
        
        new_pieces = chain(move.captures, move.placements)
        new_state.board = state.board.with_pieces(new_pieces, player)
        
        new_state.player = opponent
        new_state.moves = self.get_legal_moves(new_state.board, opponent)
        
        if len(new_state.moves) == 0:
            new_state.player = player
            new_state.moves = self.get_legal_moves(new_state.board, player)
        
        if new_state.is_over():
            new_state.winner = self.get_winner(new_state.board)
        
        return new_state
        
    def get_legal_moves(self, board: Board, player: Player):
        moves: list[Move] = []
        opponent = player.opponent()
        
        for row in range(board.size):
            for col in range(board.size):
                move = Move()
                move.position = Position(row, col)
                move.captures = []
                move.placements = [Position(row, col)]
                
                if board[row, col] != None:
                    continue
                
                for dr, dc in self.directions:
                    dir_captures: list[Position] = []
                    
                    cur_row, cur_col = self.wrap_step(board, row, col, dr, dc)
                    
                    # Caminha enquanto encontrar peças do oponente dentro do
                    # tabuleiro
                    while board[cur_row, cur_col] == opponent:
                        dir_captures.append(Position(cur_row, cur_col))
                        
                        cur_row, cur_col = self.wrap_step(board, cur_row, cur_col, dr, dc)
                    
                    # Se o loop parou e encontrou uma peça do jogador atual,
                    # fechou o oponente
                    if board[cur_row, cur_col] != player:
                        continue
                    
                    move.captures.extend(dir_captures)
                
                if len(move.captures) != 0:
                    moves.append(move)
        
        return moves
                
    def get_winner(self, board: Board):
        black_pieces = board.count_pieces(Player.BLACK)
        white_pieces = board.count_pieces(Player.WHITE)
        
        if black_pieces > white_pieces:
            return Player.BLACK
        elif white_pieces > black_pieces:
            return Player.WHITE
        else:
            return None
    
    def wrap_step(self, board: Board, row: int, col: int, dr: int, dc: int):
        nr = row + dr
        nc = col + dc
        
        if 0 <= nr < board.size and 0 <= nc < board.size:
            return nr, nc
        
        if dr > 0:
            kr = row
        elif dr < 0:
            kr = board.size - 1
        else:
            kr = float('inf')
            
        if dc > 0:
            kc = col
        elif dc < 0:
            kc = board.size - 1
        else:
            kc = float('inf')
            
        k = int(min(kr, kc))
        
        wr = row - dr * k
        wc = col - dc * k
        
        return wr, wc
