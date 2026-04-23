import time
from typing import Any

from agent import *
from game import *

class Turn:
    move: Move | None
    state: GameState
    metrics: dict[str, Any]
    
    def __init__(self, move: Move | None, state: GameState, metrics: dict[str, Any]):
        self.move = move
        self.state = state
        self.metrics = metrics

class Match:
    variant: GameVariant
    
    history: list[Turn]
    
    black_agent: Agent
    white_agent: Agent
    
    def __init__(self, variant: GameVariant, black_agent: Agent, white_agent: Agent):
        self.variant = variant
        self.history = [Turn(None, variant.create_game(), {})]
        self.black_agent = black_agent
        self.white_agent = white_agent
    
    @property
    def state(self):
        return self.history[-1].state
    
    def turn(self):
        if self.state.is_over():
            return None
        
        agent = self.get_player_agent(self.state.player)

        start_time = time.perf_counter()
        move, agent_metrics = agent.get_move(self.variant, self.state)
        end_time = time.perf_counter()

        elapsed_time = end_time - start_time
        
        if move is not None:
            metrics = {
                **agent_metrics,
                'elapsed_time': elapsed_time
            }
            
            state = self.variant.make_move(self.state, move)

            self.history.append(Turn(move, state, metrics))
        
        return move

    def play(self):
        while not self.state.is_over():
            self.turn()
        
    def restart(self, state: GameState | None = None):
        if state is None:
            state = self.variant.create_game()
        
        self.history = [Turn(None, state, {})]
    
    def get_player_agent(self, player: Player):
        if player == Player.BLACK:
            return self.black_agent
        else:
            return self.white_agent
    
    def get_agent_player(self, agent: Agent):
        if agent == self.black_agent:
            return Player.BLACK
        else:
            return Player.WHITE
