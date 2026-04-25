import numpy as np

from game import *

# A classe base que representa uma função de avaliação do jogo, sempre do ponto
# de visto do jogador das brancas.
# 
# Cada avaliador deve implementar o método params, que retorna um conjunto de
# características do tabuleiro.
#
# Cada característica é multiplicada por um peso, e a soma desses produtos é o
# valor final da pontuação do tabuleiro.
#
# O método weights é responsável por retornar os pesos atuais do avaliador, e
# também pode ser usado para atualizar os pesos.
class Evaluator:
    name: str | None
    
    def __init__(self, name: str | None = None):
        self.name = name
    
    @property
    def n(self) -> int:
        return len(self.weights())
    
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

# A classe que representa os tipos mais simples de avaliadores, que realmente
# calculam as características diretamente a partir do estado do tabuleiro,
# sem depender da combinação de outros avaliadores. Ele mantém um vetor de pesos
# próprio, que indica a importância de cada parâmetro.
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

# Avaliador de contagem de peças (material).
#
# Calcula dois parâmetros, normalizados pelo total de casas do tabuleiro:
#   1) fração de peças brancas
#   2) fração de peças pretas
#
# Os pesos padrão são [1.0, -1.0], o que faz com que a avaliação seja simplesmente
# (peças brancas - peças pretas) / total. Isso mede a vantagem material direta,
# ou seja, quanto mais peças brancas e menos pretas, melhor para as brancas.
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

# Avaliador posicional baseado em regiões fixas do tabuleiro.
#
# O tabuleiro 6x6 é dividido em 6 regiões, rotuladas de 0 a 5, de acordo com a
# tabela clássica de posições (cantos, casas C, X, A, S e centro). Para cada
# região, calcula-se a fração de peças brancas e a fração de peças pretas
# presentes nela. Os parâmetros retornados são:
#   - 6 valores: fração de peças brancas nas regiões 0 a 5
#   - 6 valores: fração de peças pretas nas mesmas regiões
#
# Os pesos padrão refletem o valor posicional tradicional do Othello:
#   Região 0 (cantos): muito valiosos -> +1.0 para brancas / -1.0 pretas.
#   Região 1 (C): casas perigosas adjacentes aos cantos -> -0.25 / +0.25.
#   Região 2 (X): casas diagonais aos cantos, também perigosas -> -0.50 / +0.50.
#   Região 3 (A): bordas centrais, valor modesto -> +0.10 / -0.10.
#   Região 4 (S): anel interno próximo ao centro -> +0.05 / -0.05.
#   Região 5 (centro): valor pequeno -> +0.01 / -0.01.
#
# Os sinais são invertidos para as peças pretas, de modo que a presença de peças
# brancas em boas posições soma positivamente, enquanto peças pretas nessas posições
# reduzem igualmente a avaliação.
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

# Avaliador de mobilidade potencial (fronteira).
#
# Uma peça é considerada "de fronteira" se está adjacente a pelo menos uma casa
# vazia. Esse conceito captura o princípio de que peças no interior, sem contato
# com vazios, costumam oferecer mais mobilidade e menos opções para o adversário.
#
# Parâmetros (normalizados pelo total de casas):
#   1) fração de peças brancas na fronteira
#   2) fração de peças pretas na fronteira
#
# Os pesos padrão são [-1.0, 1.0]. Com isso, ter menos peças brancas na fronteira
# aumenta a avaliação (contribuição negativa menor), enquanto ter mais peças
# pretas na fronteira também aumenta a avaliação. O resultado premia o jogador
# que minimiza sua própria exposição e maximiza a exposição do oponente.
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

# Avaliador de paridade.
#
# Ojogador que realiza o último movimento tem uma vantagem decisiva. Se é a vez
# das brancas e o número de casas vazias é par, as brancas farão a última jogada
# (paridade favorável). Se é a vez das pretas, a situação favorável às brancas
# ocorre quando o número de casas vazias é ímpar (paridade contra as pretas).
#
# Parâmetro único:
#   - 1.0 se a paridade atual favorece as brancas (último movimento será delas),
#     0.0 caso contrário.
#
# O peso padrão de 1.0 adiciona um bônus constante sempre que a situação de
# paridade for vantajosa para as brancas, capturando um aspecto importante do fim
# de jogo.
class ParityEvaluator(IndependentEvaluator):
    def params(self, variant: GameVariant, state: GameState):
        empty_squares = state.board.count_empty()
        
        if state.player == Player.WHITE:
            return np.array([1.0 if empty_squares % 2 == 0 else 0.0])
        else:
            return np.array([1.0 if empty_squares % 2 == 1 else 0.0])
    
    def default_weights(self):
        return np.array([1.0])

# O avaliador que combina outros avaliadores, somando suas avaliações ponderadas.
# Ele simplesmente concatena os parâmetros e pesos dos avaliadores componentes,
# permitindo criar avaliações mais complexas a partir de avaliações mais simples.
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

# Avaliador sensível à fase do jogo.
#
# Divide a partida em três fases baseadas no número de casas vazias:
#   - Abertura: mais de 22 vazias.
#   - Meio-jogo: entre 11 e 22 vazias.
#   - Final: até 10 vazias.
#
# Possui três avaliadores internos, um para cada fase. Em cada estado, apenas
# os parâmetros do avaliador da fase ativa são considerados. Os demais são
# zerados. Assim, o vetor de parâmetros é a concatenação de
# (scalar * params) para cada fase, onde o escalar é 1 na fase ativa
# e 0 nas outras.
#
# Os pesos continuam sendo a concatenação dos pesos de todos os avaliadores,
# permitindo que cada fase seja ajustada independentemente.
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

SIMPLE_COUNT_EVALUATOR = CountEvaluator(name='SCE1')

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

WRAP_AROUND_WIN_TUNED_EVALUATOR = PhaseAwareEvaluator(
    CompositeEvaluator([
        CountEvaluator([-0.13860710343627192, -0.09160050122900931]),
        PositionalEvaluator([
            0.20379642563961708, 0.7471041089787224, -0.4113114760053228, -1.8389999109619528, 0.36119395737986804, 0.42145480864596074,
            -0.41020698310759873, -0.33102802955216537, 1.0651254473081762, -0.5154740427145149, 0.29356728731919735, -0.3734534053667361
        ]),
        PotentialMobilityEvaluator([-0.36027941096024074, -0.23821912880497764]),
        ParityEvaluator([-0.14499359630605563])]),
    CompositeEvaluator([CountEvaluator([1.0989468627575907, -1.0766420439616387]),
    PositionalEvaluator([
        1.2472937570398026, 2.866890478021251, 0.34070313893801096, 0.13149566801953028, 1.0675509843747326, 0.1706506080094676,
        -0.6322955568249786, -3.487357195643616, 0.3592888765420382, -2.151636361213336, 0.727401557534303, 0.40641228327363355
    ]),
    PotentialMobilityEvaluator([-5.889247494708591, 4.911912239842629]),
    ParityEvaluator([-0.985439514278818])]),
    CompositeEvaluator([
        CountEvaluator([2.3690603356379647, -1.8031746640987474]),
        PositionalEvaluator([
            0.84080980569063, 4.420397642465156, 0.8779609927180665, 2.4126087116559956, 2.7467522658616317, 0.44325498236758415,
            0.17057249690968962, -4.150109099658508, -1.5216731151313656, -4.22570169976505, 0.9970806172914574, -0.12001099440289605
        ]),
        PotentialMobilityEvaluator([-13.457270083067666, 10.104599410055863]),
        ParityEvaluator([-1.6736275563446976])
    ]),
    name='WWTE1'
)