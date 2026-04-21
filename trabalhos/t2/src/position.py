import dataclasses

@dataclasses.dataclass
class Position:
    row: int
    col: int

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Position):
            return False
        
        return self.row == value.row and self.col == value.col