import copy
from typing import List, Iterable

from player import *
from position import *

class Board:
    size: int
    pieces: List[List[Player | None]]
    
    def __init__(self, size: int):
        self.size = size
        self.pieces = [[None] * size for _ in range(size)]
    
    def with_piece(self, row: int, col: int, player: Player | None):
        return self.with_pieces([Position(row, col)], player)
    
    def with_pieces(self, positions: Iterable[Position], player: Player | None):
        new_board = Board(self.size)
        new_board.pieces = copy.deepcopy(self.pieces)
        
        for pos in positions:
            new_board.pieces[pos.row][pos.col] = player
        
        return new_board
    
    def count_pieces(self, player: Player):
        count = 0
        
        for row in range(self.size):
            for col in range(self.size):
                if self.pieces[row][col] == player:
                    count += 1
                
        return count
    
    def __getitem__(self, key: tuple[int, int]):
        row, col = key
        
        if row < 0 or row >= self.size:
            return None
        
        if col < 0 or col >= self.size:
            return None
        
        return self.pieces[row][col]
    