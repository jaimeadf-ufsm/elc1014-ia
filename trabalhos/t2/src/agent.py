import random
import math
from typing import Self, Any

from move import *
from game import *
from evaluator import *
from provider import *

class Agent:
    @abstractmethod
    def get_move(self, variant: GameVariant, state: GameState) -> tuple[Move | None, dict[str, Any]]:
        pass
    
    def __eq__(self, value: object) -> bool:
        return isinstance(value, self.__class__)
    
    def __hash__(self) -> int:
        return hash(self.__class__)
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}()'
    
    def __repr__(self) -> str:
        return self.__str__()

class RandomAgent(Agent):
    def get_move(self, variant: GameVariant, state: GameState):
        return random.choice(state.moves), {}
    
class HumanAgent(Agent):
    provider: InputProvider
    
    def __init__(self, provider: InputProvider):
        self.provider = provider
    
    def get_move(self, variant: GameVariant, state: GameState):
        return self.provider.request_move(variant, state), {}

class MinimaxAgent(Agent):
    evaluator: Evaluator
    depth: int
    
    def __init__(self, evaluator: Evaluator, depth: int):
        self.evaluator = evaluator
        self.depth = depth
        
    def get_move(self, variant: GameVariant, state: GameState):
        metrics: dict[str, Any] = {
            'by_depth': { d: { 'nodes_explored': 0, 'nodes_pruned': 0 } for d in range(0, self.depth) }
        }
        
        score, move = self.minimax(variant, state, self.depth, float('-inf'), float('inf'), metrics)
        assert move is not None
        
        metrics['total_nodes_explored'] = sum(depth_metrics['nodes_explored'] for depth_metrics in metrics['by_depth'].values())
        metrics['total_nodes_pruned'] = sum(depth_metrics['nodes_pruned'] for depth_metrics in metrics['by_depth'].values())
        
        return move, metrics
        
    def minimax(self, variant: GameVariant, state: GameState, depth: int, alpha: float, beta: float, metrics: dict[str, Any]):
        if depth == 0 or state.is_over():
            return self.evaluator.evaluate(variant, state), None
        
        maximizing = state.player == Player.WHITE
        
        if maximizing:
            max_score = float('-inf')
            max_move = None
            
            for i, move in enumerate(state.moves):
                metrics['by_depth'][self.depth - depth]['nodes_explored'] += 1

                next_state = variant.make_move(state, move)
                next_score, _ = self.minimax(variant, next_state, depth - 1, alpha, beta, metrics)
                
                if next_score >= max_score:
                    max_score = next_score
                    max_move = move

                    alpha = max(alpha, max_score)                    
                    
                if beta <= alpha:
                    metrics['by_depth'][self.depth - depth]['nodes_pruned'] += len(state.moves) - i - 1
                    break
            
            return max_score, max_move
        else:
            min_score = float('inf')
            min_move = None
            
            for i, move in enumerate(state.moves):
                metrics['by_depth'][self.depth - depth]['nodes_explored'] += 1
                next_state = variant.make_move(state, move)
                next_score, _ = self.minimax(variant, next_state, depth - 1, alpha, beta, metrics)
                
                if next_score <= min_score:
                    min_score = next_score
                    min_move = move
                    
                    beta = min(beta, min_score)
                    
                if beta <= alpha:
                    metrics['by_depth'][self.depth - depth]['nodes_pruned'] += len(state.moves) - i - 1
                    break

            return min_score, min_move
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MinimaxAgent):
            return False
        
        return self.evaluator == value.evaluator and self.depth == value.depth
    
    def __hash__(self) -> int:
        return hash((self.__class__, self.evaluator, self.depth))
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}(evaluator={self.evaluator}, depth={self.depth})'
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(evaluator={repr(self.evaluator)}, depth={self.depth})'

class MCTSNode:
    state: GameState
    variant: GameVariant
    
    move: Move | None

    n: int
    r: dict[Player | None, int]

    parent: Self | None
    children: list['MCTSNode']
    
    untried_moves: list[Move]
    
    def __init__(self, variant: GameVariant, state: GameState, move: Move | None, parent: Self | None):
        self.variant = variant
        self.state = state
        
        self.move = move
        
        self.n = 0
        self.r = {
            Player.WHITE: 0,
            Player.BLACK: 0,
            None: 0
        }
        
        self.parent = parent
        self.children = []
        
        self.untried_moves = state.moves.copy()

    def q(self):
        assert self.parent is not None
        
        wins = self.r[self.parent.state.player]
        losses = self.r[self.parent.state.player.opponent()]
        
        return wins - losses

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
        self.n += 1
        
        if self.parent:
            self.parent.backpropagate(result)
    
    def best_child(self, c):
        best_uct = float('-inf')
        best_child = self.children[0]
        
        for child in self.children:
            uct = child.q() / child.n
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
    c: float
    
    def __init__(self, iterations: int, c: float = 1.4):
        self.iterations = iterations
        self.c = c
        
    def get_move(self, variant: GameVariant, state: GameState):
        root = MCTSNode(variant, state, None, None)
        
        for i in range(self.iterations):
            leaf = self.tree_policy(root)
            result = leaf.rollout()
            leaf.backpropagate(result)
            
        metrics = {
            'total_nodes_explored': root.n,
        }
            
        return root.best_child(0).move, metrics
    
    def tree_policy(self, root: MCTSNode):
        node = root
        
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node.expand()
            else:
                node = node.best_child(self.c)
        
        return node
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MCTSAgent):
            return False
        
        return self.iterations == value.iterations and self.c == value.c
    
    def __hash__(self) -> int:
        return hash((self.__class__, self.iterations, self.c))
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}(iterations={self.iterations}, c={self.c})'
    