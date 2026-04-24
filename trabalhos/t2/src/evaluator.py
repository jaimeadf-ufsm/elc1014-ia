from typing import Any

import numpy as np

from game import *
from game import GameState, GameVariant

class Evaluator:
    @property
    def n(self) -> int:
        return len(self.weights())
    
    # Evaluates the game always from the perspective of BLACK
    # bigger = good for BLACK
    # smaller = good for WHITE
    def evaluate(self, variant: GameVariant, state: GameState) -> float:
        if state.is_over():
            if state.winner == Player.BLACK:
                return float('inf')
            elif state.winner == Player.WHITE:
                return float('-inf')
        
        return (self.weights() * self.params(variant, state)).sum()

    @abstractmethod
    def params(self, variant: GameVariant, state: GameState) -> np.ndarray:
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
    
    def params(self, variant: GameVariant, state: GameState):
        black_pieces = state.board.count_pieces(Player.BLACK)
        white_pieces = state.board.count_pieces(Player.WHITE)
        
        count = black_pieces - white_pieces
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
            
    def params(self, variant: GameVariant, state: GameState):
        params = np.zeros(6)
        
        for i, positions in enumerate(self.labels):
            black_count = state.board.count_pieces(Player.BLACK, positions)
            white_count = state.board.count_pieces(Player.WHITE, positions)
            
            params[i] = (black_count - white_count) / positions.bit_count()
        
        return params


class PotentialMobilityEvaluator(IndependentEvaluator):
    directions: list[tuple[int, int]]
    
    def __init__(self, scale: float = 1.0):
        super().__init__(scale * np.array([1.0]))
        self.directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1) 
        ]
    
    def params(self, variant: GameVariant, state: GameState):
        black_frontier = self.compute_frontier_pieces(variant, state, Player.BLACK)
        white_frontier = self.compute_frontier_pieces(variant, state, Player.WHITE)
        
        score = (white_frontier - black_frontier) / (state.board.size * state.board.size)
        
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

class ParityEvaluator(IndependentEvaluator):
    def __init__(self, scale: float = 1.0):
        super().__init__(scale * np.array([1.0]))
    
    def params(self, variant: GameVariant, state: GameState):
        return np.array([1.0 if state.count % 2 == 0 else -1.0])

class CompoundEvaluator(Evaluator):
    evaluators: list[Evaluator]
    
    def __init__(self, evaluators: list[Evaluator]):
        self.evaluators = evaluators
    
    def evaluate(self, variant: GameVariant, state: GameState) -> float:
        return sum(e.evaluate(variant, state) for e in self.evaluators)
    
    def params(self, variant: GameVariant, state: GameState):
        return np.concatenate([e.params(variant, state) for e in self.evaluators])
    
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
    
    def params(self, variant: GameVariant, state: GameState):
        phase = self.identify_phase(state)
        components = []
        
        for scalar, e in zip(phase, self.evaluators):
            if scalar == 0:
                components.append(np.zeros(e.n))
            else:
                components.append(scalar * e.params(variant, state))
        
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
        PotentialMobilityEvaluator(0.1),
        ParityEvaluator(0.1)
    ])
)
