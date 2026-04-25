from position import *

# Estrutura que representa uma jogada legal.
#
# Um jogada é composta por:
#   - A casa onde a peça é colocada;
#   - As peças do oponente que serão viradas por flanqueamento;
#   - As casas que receberão peças do jogador.
@dataclasses.dataclass
class Move:
    position: Position
    
    captures: list[Position]
    placements: list[Position]
    
    def __init__(self):
        self.position = Position(0, 0)
        self.captures = []
        self.placements = []