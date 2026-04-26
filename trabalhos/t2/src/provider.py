import threading

from game import *

# Provedor de entrada sincronizado para jogadas humanas.
#
# Funciona como a ponte entre a interface e o a de decisão do HumanAgent,
# permitindo que o agente solicite um movimento e aguarde até que a interface
# o responda.
class InputProvider:
    condition: threading.Condition            

    game_variant: GameVariant | None
    game_state: GameState | None
    
    move: Move | None
    
    def __init__(self):
        self.condition = threading.Condition()      # Mecanismo de sincronização entre threads
        self.game_state = None
        self.game_variant = None
        self.move = None
        
    # GUI notifica a resposta
    def answer_move(self, move: Move | None):
        with self.condition:        # Adquire o lock
            self.move = move
            self.condition.notify_all()
        
    # Partida bloqueia esperando resposta
    def request_move(self, variant: GameVariant, state: GameState):
        with self.condition:
            self.game_variant = variant
            self.game_state = state
            
            self.condition.wait()
            
            # Limpa os dados
            self.game_variant = None
            self.game_state = None
            
            return self.move

    # Verifica se o provider está aguardado movimento
    def is_waiting_move(self):
        return self.game_state is not None and self.game_variant is not None
