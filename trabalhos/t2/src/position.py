import dataclasses

# Coordenada imutável (linha, coluna) dentro do tabuleiro.
@dataclasses.dataclass(frozen=True, slots=True)
class Position:
    row: int = 0
    col: int = 0
