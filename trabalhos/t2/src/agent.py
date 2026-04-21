import random
import math
from typing import Self

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
            

class MCTSNode:
    state: GameState
    variant: GameVariant
    
    move: Move | None

    q: int
    n: int

    parent: Self | None
    children: list['MCTSNode']
    
    untried_moves: list[Move]
    
    def __init__(self, variant: GameVariant, state: GameState, move: Move | None, parent: Self | None):
        self.variant = variant
        self.state = state
        
        self.move = move
        
        self.q = 0
        self.n = 0
        
        self.parent = parent
        self.children = []
        
        self.untried_moves = state.moves.copy()

    def expand(self):
        next_move = self.untried_moves.pop()
        
        next_state = self.variant.make_move(self.state, next_move)
        next_node = MCTSNode(self.variant, next_state, next_move, self)
        
        self.children.append(next_node)
        
        return next_node
    
    def rollout(self):
        state = self.state
        
        while not state.is_over():
            move = self.rollout_policy(state)
            state = self.variant.make_move(state, move)
        
        return state.winner

    def rollout_policy(self, state: GameState):
        return random.choice(state.moves)

    def backpropagate(self, result: Player | None):
        if result == self.state.player.opponent():
            self.q += 1
        elif result == self.state.player:
            self.q -= 1
            
        self.n += 1
        
        if self.parent:
            self.parent.backpropagate(result)
    
    def best_child(self, c=1.4):
        best_uct = float('-inf')
        best_child = self.children[0]
        
        for child in self.children:
            uct = child.q / child.n
            uct += c * math.sqrt(math.log(self.n) / child.n)
            
            if uct > best_uct:
                best_uct = uct
                best_child = child
        
        return best_child
    
    def is_terminal(self):
        return self.state.is_over()
    
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
            
class MCTSAgent(Agent):
    iterations: int
    
    def __init__(self, iterations: int):
        self.iterations = iterations
        
    def get_move(self, variant: GameVariant, state: GameState) -> Move | None:
        root = MCTSNode(variant, state, None, None)
        
        for i in range(self.iterations):
            leaf = self.tree_policy(root)
            result = leaf.rollout()
            leaf.backpropagate(result)
            
        # if c_param is 0.0, it only considers the score for exploitation
        return root.best_child(0).move
    
    def tree_policy(self, root: MCTSNode):
        node = root
        
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node.expand()
            else:
                node = node.best_child()
        
        return node
    