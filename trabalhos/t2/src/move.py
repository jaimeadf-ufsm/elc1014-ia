from position import *

@dataclasses.dataclass
class Move:
    position: Position
    
    captures: list[Position]
    placements: list[Position]
    
    def __init__(self):
        self.position = Position(0, 0)
        self.captures = []
        self.placements = []