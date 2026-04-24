from typing import Any

import numpy as np

from game import *
from game import GameState, GameVariant

class Evaluator:
    @property
    def n(self) -> int:
        return len(self.weights())
    
    def evaluate(self, variant: GameVariant, state: GameState, player: Player) -> float:
        if state.is_over() and state.winner is not None:
            if state.winner == player:
                return float('inf')
            else:
                return float('-inf')
        
        return (self.weights() * self.params(variant, state, player)).sum()

    @abstractmethod
    def params(self, variant: GameVariant, state: GameState, player: Player) -> np.ndarray:
        pass
    
    @abstractmethod
    def weights(self, values: np.ndarray | None = None) -> np.ndarray:
        pass
        
    def __eq__(self, value: object) -> bool:
        return isinstance(value, self.__class__)
    
    def __hash__(self) -> int:
        return hash(self.__class__)
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}()'

class IndependentEvaluator(Evaluator):
    def __init__(self, w: np.ndarray):
        self.w = w
    
    def weights(self, values: np.ndarray | None = None) -> np.ndarray:
        if values is not None:
            self.w = values
            
        return self.w

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(w={self.w})'

class CountEvaluator(IndependentEvaluator):
    def __init__(self, scale: float = 1.0):
        super().__init__(np.array([scale]))
    
    def params(self, variant: GameVariant, state: GameState, player: Player):
        player_pieces = state.board.count_pieces(player)
        opponent_pieces = state.board.count_pieces(player.opponent())
        
        count = player_pieces - opponent_pieces
        ratio = count / (state.board.size * state.board.size)
        
        return np.array((ratio,))

class PositionalEvaluator(IndependentEvaluator):
    def __init__(self, scale: float = 1.0):
        super().__init__(scale * np.array([1, -0.25, -0.50, 0.10, 0.05, 0.01]))
        
        #   0  1  2  3  4  5
        # 0 Q  C  A  A  C  Q
        # 1 C  X  S  S  X  C
        # 2 A  S  M  M  S  A
        # 3 A  S  M  M  S  A
        # 4 C  X  S  S  X  C
        # 5 Q  C  A  A  C  Q
        table = [
            [0, 1, 3, 3, 1, 0],
            [1, 2, 4, 4, 2, 1],
            [3, 4, 5, 5, 4, 3],
            [3, 4, 5, 5, 4, 3],
            [1, 2, 4, 4, 2, 1],
            [0, 1, 3, 3, 1, 0],
        ]
        
        self.labels = [0] * 6
        
        for row, indices in enumerate(table):
            for col, index in enumerate(indices):
                self.labels[index] |= (1 << (row * 6 + col))
            
    def params(self, variant: GameVariant, state: GameState, player: Player):
        params = np.zeros(6)
        
        player = player
        opponent = player.opponent()
        
        for i, positions in enumerate(self.labels):
            player_pieces = state.board.count_pieces(player, positions)
            opponent_pieces = state.board.count_pieces(opponent, positions)
            
            params[i] = (player_pieces - opponent_pieces) / positions.bit_count()
        
        return params

class PotentialMobilityEvaluator(IndependentEvaluator):
    directions: list[tuple[int, int]]
    
    def __init__(self, scale: float = 1.0):
        super().__init__(scale * np.array([1.0]))
        self.directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1) 
        ]
    
    def params(self, variant: GameVariant, state: GameState, player: Player):
        player_frontier = self.compute_frontier_pieces(variant, state, player)
        opponent_frontier = self.compute_frontier_pieces(variant, state, player.opponent())
        
        score = (opponent_frontier - player_frontier) / (state.board.size * state.board.size)
        
        return np.array([score])
    
    def compute_frontier_pieces(self, variant: GameVariant, state: GameState, player: Player):
        # Uma peça é considerada "fronteiriça" se estiver adjacente a pelo
        # menos uma casa vazia
        frontier_pieces = 0
        
        for row in range(state.board.size):
            for col in range(state.board.size):
                piece = state.board[row, col]
                
                if piece != player:
                    continue
                
                for dr, dc in self.directions:
                    if isinstance(variant, WrapAroundGameVariant):
                        r, c = variant.wrap_step(state.board, row, col, dr, dc)
                    else:
                        r, c = row + dr, col + dc
                    
                    if 0 <= r < state.board.size and 0 <= c < state.board.size:
                        if state.board[r, c] is None:
                            frontier_pieces += 1
                            break
        
        return frontier_pieces

class CompoundEvaluator(Evaluator):
    evaluators: list[Evaluator]
    
    def __init__(self, evaluators: list[Evaluator]):
        self.evaluators = evaluators
    
    def evaluate(self, variant: GameVariant, state: GameState, player: Player):
        return sum(e.evaluate(variant, state, player) for e in self.evaluators)
    
    def params(self, variant: GameVariant, state: GameState, player: Player):
        return np.concatenate([e.params(variant, state, player) for e in self.evaluators])
    
    def weights(self, values: np.ndarray | None = None):
        if values is not None:
            index = 0
            
            for e in self.evaluators:
                e.weights(values[index:index+e.n])
                index += e.n
                
        return np.concatenate([e.weights() for e in self.evaluators])

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({", ".join(str(e) for e in self.evaluators)})'

class PhaseAwareEvaluator(Evaluator):
    evaluators: list[Evaluator]
        
    def __init__(self, opening_evaluator: Evaluator, midgame_evaluator: Evaluator, endgame_evaluator: Evaluator):
        super().__init__()
        self.evaluators = [opening_evaluator, midgame_evaluator, endgame_evaluator]
    
    def params(self, variant: GameVariant, state: GameState, player: Player):
        phase = self.identify_phase(state)
        components = []
        
        for scalar, e in zip(phase, self.evaluators):
            if scalar == 0:
                components.append(np.zeros(e.n))
            else:
                components.append(scalar * e.params(variant, state, player))
        
        return np.concatenate(components)
    
    def weights(self, values: np.ndarray | None = None):
        if values is not None:
            index = 0
            
            for e in self.evaluators:
                e.weights(values[index:index+e.n])
                index += e.n
                
        return np.concatenate([e.weights() for e in self.evaluators])
     
    def identify_phase(self, state: GameState):
        empty_count = state.board.count_empty()
        
        if empty_count > 22:
            return (1, 0, 0)
        elif empty_count > 10:
            return (0, 1, 0)
        else:
            return (0, 0, 1)
        
    def __str__(self) -> str:
        return f'{self.__class__.__name__}({", ".join(str(e) for e in self.evaluators)})'

DIEGO_EVALUATOR = PhaseAwareEvaluator(
    opening_evaluator=CompoundEvaluator([
        PositionalEvaluator(0.4),
        CountEvaluator(0.2),
        PotentialMobilityEvaluator(0.2)
    ]),
    midgame_evaluator=CompoundEvaluator([
        PositionalEvaluator(0.3),
        CountEvaluator(0.4),
        PotentialMobilityEvaluator(0.2)
    ]),
    endgame_evaluator=CompoundEvaluator([
        CountEvaluator(0.7),
        PositionalEvaluator(0.2),
        PotentialMobilityEvaluator(0.1)
    ])
)
