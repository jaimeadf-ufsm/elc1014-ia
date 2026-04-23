import enum

class Player(enum.Enum):
    BLACK = 1
    WHITE = 2
    
    def opponent(self):
        return Player.WHITE if self == Player.BLACK else Player.BLACK 
    
    def __str__(self) -> str:
        return 'Preto' if self == Player.BLACK else 'Branco'
