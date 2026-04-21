import random

from move import *
from game import *
from evaluator import *
from provider import *

class Agent:
    @abstractmethod
    def get_move(self, variant: GameVariant, state: GameState) -> Move | None:
        pass

class RandomAgent(Agent):
    def get_move(self, variant: GameVariant, state: GameState) -> Move | None:
        return random.choice(state.moves)

class HumanAgent(Agent):
    provider: InputProvider
    
    def __init__(self, provider: InputProvider):
        self.provider = provider
    
    def get_move(self, variant: GameVariant, state: GameState) -> Move | None:
        return self.provider.request_move(variant, state)

class MinimaxAgent(Agent):
    evaluator: Evaluator
    depth: int
    
    def __init__(self, evaluator: Evaluator, depth: int):
        self.evaluator = evaluator
        self.depth = depth
        
    def get_move(self, variant: GameVariant, state: GameState) -> Move | None:
        score, move = self.minimax(variant, state, state.player, self.depth, float('-inf'), float('inf'))
        assert move is not None
        
        return move
        
    def minimax(self, variant: GameVariant, state: GameState, player: Player, depth: int, alpha: float, beta: float):
        if depth == 0 or state.is_over():
            return self.evaluator.evaluate(variant, state, player), None
        
        maximizing = state.player == player
        
        if maximizing:
            max_score = float('-inf')
            max_move = None
            
            for move in state.moves:
                next_state = variant.make_move(state, move)
                next_score, _ = self.minimax(variant, next_state, player, depth - 1, alpha, beta)
                
                if next_score > max_score:
                    max_score = next_score
                    max_move = move

                    alpha = max(alpha, max_score)                    
                    
                if beta <= alpha:
                    break
            
            return max_score, max_move
        else:
            min_score = float('inf')
            min_move = None
            
            for move in state.moves:
                next_state = variant.make_move(state, move)
                next_score, _ = self.minimax(variant, next_state, player, depth - 1, alpha, beta)
                
                if next_score < min_score:
                    min_score = next_score
                    min_move = move
                    
                    beta = min(beta, min_score)
                    
                if beta <= alpha:
                    break

            return min_score, min_move
            
            
            
            