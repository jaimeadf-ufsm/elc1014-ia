from agent import *
from game import *

class Engine:
    game_variant: GameVariant
    game_state: GameState

    black_agent: Agent
    white_agent: Agent
    
    def __init__(self, game_variant: GameVariant, black_agent: Agent, white_agent: Agent) -> None:
        self.game_variant = game_variant
        self.game_state = game_variant.create_game()
        self.black_agent = black_agent
        self.white_agent = white_agent
    
    def tick(self):
        if self.game_state.is_over():
            return None
        
        agent = self.get_playing_agent()
        move = agent.get_move(self.game_variant, self.game_state)
        
        if move is not None:
            self.game_state = self.game_variant.make_move(self.game_state, move)
        
        return move
    
    def restart(self):
        self.game_state = self.game_variant.create_game()
        
    def get_playing_agent(self):
        if self.game_state.player == Player.BLACK:
            return self.black_agent
        else:
            return self.white_agent
    