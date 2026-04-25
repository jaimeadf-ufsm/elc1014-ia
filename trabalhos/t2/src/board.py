from typing import Iterable

from player import *
from position import *

# Representação do tabuleiro do Othello usando bitboards.
#
# O estado do tabuleiro é mantido em dois inteiros (white_pieces e black_pieces),
# onde cada bit representa uma casa (row * size + col). Essa estrutura
# torna contagens e consultas rápidas e facilita o uso em simulacões.
#
# As operações `with_piece` e `with_pieces`  retornam um novo tabuleiro,
# permitindo tratar o tabuleiro como imutável enquanto o motor gera estados
# sucessores.
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
        
        bitmask = self.mask_of(positions)
            
        if player == Player.WHITE:
            new_board.white_pieces |= bitmask
            new_board.black_pieces &= ~bitmask
        elif player == Player.BLACK:
            new_board.black_pieces |= bitmask
            new_board.white_pieces &= ~bitmask
        
        return new_board
    
    def count_pieces(self, player: Player | None = None, positions: Iterable[Position] | Position | int | None = None):
        bitmask = self.mask_of(positions)
        
        if player == Player.WHITE:
            return (self.white_pieces & bitmask).bit_count()
        elif player == Player.BLACK:
            return (self.black_pieces & bitmask).bit_count()
        else:
            return ((self.white_pieces | self.black_pieces) & bitmask).bit_count()
    
    def count_empty(self, positions: Iterable[Position] | Position | int | None = None):
        bitmask = self.mask_of(positions)
        
        return ((~(self.white_pieces | self.black_pieces)) & bitmask).bit_count()

    def mask_of(self, positions: Iterable[Position] | Position | int | None = None):
        if positions is None:
            return (1 << (self.size * self.size)) - 1

        if isinstance(positions, Position):
            positions = (positions,)
        
        if isinstance(positions, int):
            return positions
        
        bitmask = 0
        
        for pos in positions:
            bitmask |= 1 << (pos.row * self.size + pos.col)
        
        return bitmask
    
    def __getitem__(self, key: tuple[int, int]):
        row, col = key
        
        if row < 0 or row >= self.size:
            return None
        
        if col < 0 or col >= self.size:
            return None
        
        bitmask = self.mask_of(Position(row, col))
        
        if self.white_pieces & bitmask != 0:
            return Player.WHITE
        elif self.black_pieces & bitmask != 0:
            return Player.BLACK
        else:
            return None
