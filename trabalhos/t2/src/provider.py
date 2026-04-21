import threading

from game import *

class InputProvider:
    condition: threading.Condition

    game_variant: GameVariant | None
    game_state: GameState | None
    
    move: Move | None
    
    def __init__(self):
        self.condition = threading.Condition()
        self.game_state = None
        self.game_variant = None
        self.move = None
        
    def answer_move(self, move: Move | None):
        with self.condition:
            self.move = move
            self.condition.notify_all()
        
    def request_move(self, variant: GameVariant, state: GameState):
        with self.condition:
            self.game_variant = variant
            self.game_state = state
            
            self.condition.wait()
            
            self.game_variant = None
            self.game_state = None
            
            return self.move

    def is_waiting_move(self):
        return self.game_state is not None and self.game_variant is not None
