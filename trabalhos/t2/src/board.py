import copy
from typing import Iterable

from player import *
from position import *

class Board:
    size: int
    white_pieces: int
    black_pieces: int
    
    def __init__(self, size: int):
        self.size = size
        self.white_pieces = 0
        self.black_pieces = 0
    
    def with_piece(self, row: int, col: int, player: Player | None):
        return self.with_pieces([Position(row, col)], player)
    
    def with_pieces(self, positions: Iterable[Position], player: Player | None):
        new_board = Board(self.size)
        new_board.white_pieces = self.white_pieces
        new_board.black_pieces = self.black_pieces
        
        for pos in positions:
            bitmask = self.piece_bitmask(pos.row, pos.col)
            
            if player == Player.WHITE:
                new_board.white_pieces |= bitmask
                new_board.black_pieces &= ~bitmask
            elif player == Player.BLACK:
                new_board.black_pieces |= bitmask
                new_board.white_pieces &= ~bitmask
        
        return new_board
    
    def count_pieces(self, player: Player):
        if player == Player.WHITE:
            return self.white_pieces.bit_count()
        else:
            return self.black_pieces.bit_count()

    def piece_bitmask(self, row: int, col: int):
        return 1 << (row * self.size + col)
    
    def __getitem__(self, key: tuple[int, int]):
        row, col = key
        
        if row < 0 or row >= self.size:
            return None
        
        if col < 0 or col >= self.size:
            return None
        
        bitmask = self.piece_bitmask(row, col)
        
        if self.white_pieces & bitmask != 0:
            return Player.WHITE
        elif self.black_pieces & bitmask != 0:
            return Player.BLACK
        else:
            return None
