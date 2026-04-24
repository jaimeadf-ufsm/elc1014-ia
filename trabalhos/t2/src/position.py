import dataclasses

@dataclasses.dataclass(frozen=True, slots=True)
class Position:
    row: int = 0
    col: int = 0
