import numpy as np

from game import *

class Evaluator:
    name: str | None
    
    def __init__(self, name: str | None = None):
        self.name = name
    
    @property
    def n(self) -> int:
        return len(self.weights())
    
    # Evaluates the given game state from the perspective of the WHITE player:
    # - Positive values indicate an advantage for WHITE
    # - negative values indicate an advantage for BLACK.
    def evaluate(self, variant: GameVariant, state: GameState) -> float:
        if state.is_over() and state.winner is not None:
            if state.winner == Player.WHITE:
                return float('inf')
            else:
                return float('-inf')
        
        return (self.weights() * self.params(variant, state)).sum()

    @abstractmethod
    def params(self, variant: GameVariant, state: GameState) -> np.ndarray:
        pass
    
    @abstractmethod
    def weights(self, w: list[float] |np.ndarray | None = None) -> np.ndarray:
        pass
    
    @abstractmethod
    def default_weights(self) -> np.ndarray:
        pass
        
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False
        
        return self.name == value.name and np.array_equal(self.weights(), value.weights())
    
    def __hash__(self) -> int:
        return hash(self.__class__)
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}()'
    
    def __repr__(self) -> str:
        if self.name is not None:
            return f'{self.__class__.__name__}(name="{self.name}")'
        
        return str(self)

class IndependentEvaluator(Evaluator):
    def __init__(self, w: list[float] | np.ndarray | None = None, scale: float = 1.0, name: str | None = None):
        super().__init__(name)
        
        if w is None:
            w = self.default_weights()
            
        self.w = scale * np.array(w)
    
    def weights(self, w: list[float] | np.ndarray | None = None):
        if w is not None:
            self.w = np.array(w)
            
        return self.w

    def __str__(self) -> str:
        return f'{self.__class__.__name__}([{", ".join(f"{weight}" for weight in self.w)}])'

class CountEvaluator(IndependentEvaluator):
    def params(self, variant: GameVariant, state: GameState):
        total_pieces = state.board.size * state.board.size

        white_pieces = state.board.count_pieces(Player.WHITE)
        black_pieces = state.board.count_pieces(Player.BLACK)
        
        white_pieces /= total_pieces
        black_pieces /= total_pieces
        
        return np.array((white_pieces, black_pieces))

    def default_weights(self):
        return np.array([1.0, -1.0])

class PositionalEvaluator(IndependentEvaluator):
    def __init__(self, w: list[float] | np.ndarray | None = None, scale: float = 1.0, name: str | None = None):
        super().__init__(w, scale, name)
        
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
        n = len(self.labels)
        params = np.zeros(2 * len(self.labels))
        
        for i, positions in enumerate(self.labels):
            white_pieces = state.board.count_pieces(Player.WHITE, positions)
            black_pieces = state.board.count_pieces(Player.BLACK, positions)
            
            params[i] = white_pieces / positions.bit_count()
            params[i + n] = black_pieces / positions.bit_count()
        
        return params
    
    def default_weights(self):
        return np.array([
            1, -0.25, -0.50, 0.10, 0.05, 0.01,
            -1, 0.25, 0.50, -0.10, -0.05, -0.01
        ])

class PotentialMobilityEvaluator(IndependentEvaluator):
    directions: list[Tuple[int, int]]
    
    def __init__(self, w: list[float] | np.ndarray | None = None, scale: float = 1.0, name: str | None = None):
        super().__init__(w, scale, name)
        self.directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1) 
        ]
    
    def params(self, variant: GameVariant, state: GameState):
        total_pieces = state.board.size * state.board.size
        
        white_pieces = self.compute_frontier_pieces(variant, state, Player.WHITE)
        black_pieces = self.compute_frontier_pieces(variant, state, Player.BLACK)
        
        white_pieces /= total_pieces
        black_pieces /= total_pieces
        
        return np.array((white_pieces, black_pieces))
    
    def default_weights(self):
        return np.array([-1.0, 1.0])
    
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
    def params(self, variant: GameVariant, state: GameState):
        empty_squares = state.board.count_empty()
        
        if state.player == Player.WHITE:
            return np.array([1.0 if empty_squares % 2 == 0 else 0.0])
        else:
            return np.array([1.0 if empty_squares % 2 == 1 else 0.0])
    
    def default_weights(self):
        return np.array([1.0])

class CompositeEvaluator(Evaluator):
    evaluators: list[Evaluator]
    
    def __init__(self, evaluators: list[Evaluator], name: str | None = None):
        super().__init__(name)
        self.evaluators = evaluators
    
    def evaluate(self, variant: GameVariant, state: GameState):
        return sum(e.evaluate(variant, state) for e in self.evaluators)
    
    def params(self, variant: GameVariant, state: GameState):
        return np.concatenate([e.params(variant, state) for e in self.evaluators])
    
    def weights(self, w: list[float] | np.ndarray | None = None):
        if w is not None:
            index = 0
            
            for e in self.evaluators:
                e.weights(w[index:index+e.n])
                index += e.n
                
        return np.concatenate([e.weights() for e in self.evaluators])
    
    def default_weights(self):
        return np.concatenate([e.default_weights() for e in self.evaluators])

    def __str__(self) -> str:
        return f'{self.__class__.__name__}([{", ".join(str(e) for e in self.evaluators)}])'

class PhaseAwareEvaluator(Evaluator):
    evaluators: list[Evaluator]
        
    def __init__(self, opening: Evaluator, midgame: Evaluator, endgame: Evaluator, name: str | None = None):
        super().__init__(name)
        self.evaluators = [opening, midgame, endgame]
    
    def params(self, variant: GameVariant, state: GameState):
        phase = self.identify_phase(state)
        components = []
        
        for scalar, e in zip(phase, self.evaluators):
            if scalar == 0:
                components.append(np.zeros(e.n))
            else:
                components.append(scalar * e.params(variant, state))
        
        return np.concatenate(components)
    
    def weights(self, w: list[float] | np.ndarray | None = None):
        if w is not None:
            index = 0
            
            for e in self.evaluators:
                e.weights(w[index:index+e.n])
                index += e.n
                
        return np.concatenate([e.weights() for e in self.evaluators])
    
    def default_weights(self):
        return np.concatenate([e.default_weights() for e in self.evaluators])
     
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

CLASSICAL_EMPIRIC_EVALUATOR = PhaseAwareEvaluator(
    opening=CompositeEvaluator([
        PositionalEvaluator(scale=0.4),
        CountEvaluator(scale=0.2),
        PotentialMobilityEvaluator(scale=0.2)
    ]),
    midgame=CompositeEvaluator([
        PositionalEvaluator(scale=0.3),
        CountEvaluator(scale=0.4),
        PotentialMobilityEvaluator(scale=0.2)
    ]),
    endgame=CompositeEvaluator([
        CountEvaluator(scale=0.7),
        PositionalEvaluator(scale=0.2),
        PotentialMobilityEvaluator(scale=0.1)
    ]),
    name='CEE1'
)

CLASSICAL_WIN_TUNED_EVALUATOR = PhaseAwareEvaluator(
    CompositeEvaluator([
        CountEvaluator([0.3973098507079885, -0.14860314043300984]),
        PositionalEvaluator([
            9.443434940036791, -1.9447575145197502, -5.570319916595326, 2.9508230011769774, -1.3394771887199561, 0.36949703705589004,
            -10.371747284050013, 3.5645205721822015, 3.6275842879159197, -2.036858461263868, 0.9409195250334728, 0.4695714603334972
        ]),
        PotentialMobilityEvaluator([0.17689006141365293, -0.2541501721022306]),
        ParityEvaluator([0.0])
    ]),
    CompositeEvaluator([
        CountEvaluator([1.7978671365036396, -1.710181440813928]),
        PositionalEvaluator([
            7.179486833849543, 2.1103799069925673, -1.4607773037976133, 2.5722930718455244, 0.180831565824716, 0.7350856091551453,
            -8.770963421856136, -1.915171169932762, 2.4821990126581386, -1.7212690907078467, -0.6488856650023427, -0.5322167068416442
        ]),
        PotentialMobilityEvaluator([-8.379758416983124, 8.863010182921196]),
        ParityEvaluator([-2.2810115646604987])]),
    CompositeEvaluator([
        CountEvaluator([2.1257131954951727, -1.747044938066023]),
        PositionalEvaluator([
            4.957019271786092, 3.642243273856456, 0.07881920890682434, 2.5586624628528343, 1.1396906442782844, -0.5856124832116602,
            -4.624749485725917, -3.5355105011812444, 0.4319521787469469, -0.9312102735614655, -0.511679308442467, -1.5738069692450647
        ]),
        PotentialMobilityEvaluator([-12.268261753596644, 12.536438420474637]), 
        ParityEvaluator([-1.537864749453391])
    ]),
    name='CWTE1'
)

CLASSICAL_SCORE_TUNED_EVALUATOR = PhaseAwareEvaluator(
    CompositeEvaluator([
        CountEvaluator([14.516142853514316, 1.9022305431256068]),
        PositionalEvaluator([
             58.37410517642907, 7.3667796959134115, -21.059438762590304, 27.796555641358385, 6.885458919503797, 9.23303075423799,
            -51.806487486009964, 21.797498072639904, 19.573710071264596, -6.370212487835802, 6.527040307735127, 5.4442005177973325
        ]),
        PotentialMobilityEvaluator([-71.31411546818677, -21.641555096470846]),
        ParityEvaluator([7.105427357601002e-14])
    ]),
    CompositeEvaluator([
        CountEvaluator([8.041776499836491, -7.546505875782553]),
        PositionalEvaluator([
            25.851775653635798, 11.805921402668595, -4.545497848828328, 9.089774474239185, 2.6866637184874103, 3.904991502931953,
            -31.529649731606156, -7.783739776579703, 5.6996086326394355, -8.516245686016848, -4.894342518709051, 0.3001441795352189
        ]),
        PotentialMobilityEvaluator([-35.55974199279573, 37.1423863030642]),
        ParityEvaluator([-10.684122695771778])
    ]),
    CompositeEvaluator([
        CountEvaluator([5.3223925501119265, -5.722247644294874]),
        PositionalEvaluator([
            14.24305373532203, 8.412746522937505, -0.2932241754953588, 5.653614373101832, -1.3089942845052456, 8.436970168113177,
            -13.420437682706922, -9.027564492653601, -1.5937636615639907, -4.3268424039334406, -8.184450154481294, 6.591686647754889
        ]),
        PotentialMobilityEvaluator([-38.30627200962606, 34.238931844498794]),
        ParityEvaluator([-4.063103695321542])
    ]),
    name='CSTE1'
)