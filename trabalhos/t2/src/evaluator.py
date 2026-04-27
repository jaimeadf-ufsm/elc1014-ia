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
    
    # Número total de parametros
    @property
    def n(self) -> int:
        return len(self.weights())
    
    def evaluate(self, variant: GameVariant, state: GameState) -> float:
        # Estado final, alguém ganhou
        if state.is_over() and state.winner is not None:
            if state.winner == Player.WHITE:
                return float('inf')
            else:
                return float('-inf')
        
        # Calcula pontuação
        return (self.weights() * self.params(variant, state)).sum()

    # Calcula características do estado
    @abstractmethod
    def params(self, variant: GameVariant, state: GameState) -> np.ndarray:
        pass
    
    # Retorna/atualiza os pesos
    @abstractmethod
    def weights(self, w: list[float] |np.ndarray | None = None) -> np.ndarray:
        pass
    
    # Pesos padrão iniciais
    @abstractmethod
    def default_weights(self) -> np.ndarray:
        pass
        
    # Dois avaliadores são iguais se: mesmo nome e mesmos pesos
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
    
    # Setter/getter: permite atualizar ou retornar os pesos
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
        
        # Agrupa bitboards com todas as casas da região i
        for row, indices in enumerate(table):
            for col, index in enumerate(indices):
                self.labels[index] |= (1 << (row * 6 + col))
            
    def params(self, variant: GameVariant, state: GameState):
        n = len(self.labels)
        # Terá 12 elementos: 6 para as brancas + 6 para as pretas
        params = np.zeros(2 * len(self.labels))
        
        for i, positions in enumerate(self.labels):
            white_pieces = state.board.count_pieces(Player.WHITE, positions)
            black_pieces = state.board.count_pieces(Player.BLACK, positions)
            
            # Armazena em params[i] as brancas e params[i + n] as pretas (contagem normalizada)
            params[i] = white_pieces / positions.bit_count()
            params[i + n] = black_pieces / positions.bit_count()
        
        return params
    
    def default_weights(self):
        return np.array([
            1, -0.25, -0.50, 0.10, 0.05, 0.01,      # Brancas
            -1, 0.25, 0.50, -0.10, -0.05, -0.01     # Pretas
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
    
    # Conta peças de fronteira (cada cor), normaliza pelo total de casas, retorna as frações
    def params(self, variant: GameVariant, state: GameState):
        total_pieces = state.board.size * state.board.size
        
        white_pieces = self.compute_frontier_pieces(variant, state, Player.WHITE)
        black_pieces = self.compute_frontier_pieces(variant, state, Player.BLACK)
        
        white_pieces /= total_pieces
        black_pieces /= total_pieces
        
        return np.array((white_pieces, black_pieces))
    
    # Favorável quando brancas tem poucas peças de fronteira e pretas têm peças de fronteira
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
# O jogador que realiza o último movimento tem uma vantagem decisiva. Se é a vez
# das brancas e o número de casas vazias é par, as pretas farão a última jogada
# (paridade desfavorável). Se é a vez das pretas, a situação desfavorável às brancas
# ocorre quando o número de casas vazias é ímpar.
#
# Parâmetro único:
#   - 1.0 se a paridade atual desfavorece as brancas (último movimento será delas),
#     0.0 caso contrário.
#
# O peso padrão de -1.0 adiciona um bônus constante sempre que a situação de
# paridade for desvantajosa para as brancas, capturando um aspecto importante do
# fim de jogo.
class ParityEvaluator(IndependentEvaluator):
    def params(self, variant: GameVariant, state: GameState):
        empty_squares = state.board.count_empty()
        
        if state.player == Player.WHITE:
            return np.array([1.0 if empty_squares % 2 == 0 else 0.0])
        else:
            return np.array([1.0 if empty_squares % 2 == 1 else 0.0])
    
    def default_weights(self):
        return np.array([-1.0])

# O avaliador que combina outros avaliadores, somando suas avaliações ponderadas.
# Ele simplesmente concatena os parâmetros e pesos dos avaliadores componentes,
# permitindo criar avaliações mais complexas a partir de avaliações mais simples.
class CompositeEvaluator(Evaluator):
    evaluators: list[Evaluator]
    
    def __init__(self, evaluators: list[Evaluator], name: str | None = None):
        super().__init__(name)
        self.evaluators = evaluators        # Lista de avaliadores componentes
    
    def evaluate(self, variant: GameVariant, state: GameState):
        return sum(e.evaluate(variant, state) for e in self.evaluators)
    
    def params(self, variant: GameVariant, state: GameState):
        return np.concatenate([e.params(variant, state) for e in self.evaluators])
    
    # Getter/setter
    def weights(self, w: list[float] | np.ndarray | None = None):
        if w is not None:
            index = 0
            
            # Atualiza pesos distributivamente
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
        
        # Ex.:
        # Meio-jogo ativo (fase = 0, 1, 0):

        # components = [
        #   zeros(6),                           # abertura: zerada
        #   midgame.params([...]),              # meio-jogo: valores reais
        #   zeros(6)                            # fim do jogo: zerada
        # ]

        # params totais: [0,0,0,0,0,0, valores, 0,0,0,0,0,0]

        for scalar, e in zip(phase, self.evaluators):
            # Fase inativa (scalar=0) sem contribuição
            if scalar == 0:
                components.append(np.zeros(e.n))
            # Fase ativa (scalar=1) adiciona parâmetros ao avaliador
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
            return (1, 0, 0)        # Abertura
        elif empty_count > 10:
            return (0, 1, 0)        # Meio-jogo
        else:
            return (0, 0, 1)        # Fim do jogo
        
    def __str__(self) -> str:
        return f'{self.__class__.__name__}({", ".join(str(e) for e in self.evaluators)})'


# Avaliadores pré-configurados
SIMPLE_COUNT_EVALUATOR = CountEvaluator(name='SCE1')

# Baseado em conhecimento clássico do Othello, diferentes pesos por fase
# Abertura valoriza posição, meio-jogo valoriza contagem etc
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

# Pesos ajustados para maximizar vitórias (por aprendizado)
CLASSICAL_WIN_TUNED_EVALUATOR = PhaseAwareEvaluator(
    CompositeEvaluator([
        CountEvaluator([0.16429113017792984, -0.05656811674869226]),
        PositionalEvaluator([
            6.692414620039111, -0.6933008635046655, -4.507695346694164, 1.9109145894114508, -2.010563121515271, 0.8797996894733735,
            -8.363472300308281, 2.7359252202081414, 2.3168144746930506, -1.4087013366674979, 1.1890951684086732, 0.5049066709783707
        ]),
        PotentialMobilityEvaluator([0.22036291167694008, 0.0008220676403655359]),
        ParityEvaluator([0.3500528573248377])
    ]),
    CompositeEvaluator([
        CountEvaluator([1.177038129951712, -1.1236951315467039]),
        PositionalEvaluator([
            5.729060583761908, 2.4405892315968543, -1.9797058734701019, 1.903804755841784, -1.344563606378661, 0.8443276971536207,
            -6.620540041497472, -2.0274709942443434, 1.4207560817985077, -0.9687393512291999, 0.5378559105885342, 0.0032366455486529215
        ]),
        PotentialMobilityEvaluator([-5.141476154122081, 5.775352200723444]),
        ParityEvaluator([-0.15398546644715258])]),
    CompositeEvaluator([
        CountEvaluator([1.8117968109993885, -1.6469909644009566]),
        PositionalEvaluator([
            4.057443401104449, 4.629309492791601, -0.3011605134705872, 2.0683127815036837, -0.8965481855684398, 0.9477402339069969,
            -4.080770689889747, -2.7009134734336206, 0.4176933481044709, -1.2996737326198151, -1.431458365818441, -0.2957501940795301
        ]),
        PotentialMobilityEvaluator([-11.23868681517796, 12.242408185599873]),
        ParityEvaluator([-0.3972316860919512])
    ]),
    name='CWTE1'
)

# Pesos ajustados para maximizar diferença de pontuação final
CLASSICAL_SCORE_TUNED_EVALUATOR = PhaseAwareEvaluator(
    CompositeEvaluator([
        CountEvaluator([-0.8730004454012975, -17.111291978317368]),
        PositionalEvaluator([
            65.58356535128586, -15.127892640299049, -38.36781983864511, 8.836401368911066, -12.125243653054515, 1.760720327631613,
            -79.93186904804519, 10.455723170004658, 9.9197323093744, -31.158975320414985, -18.472497238057343, -5.637992289262723
        ]),
        PotentialMobilityEvaluator([19.759365290789862, 111.91790175658471]),
        ParityEvaluator([0.028493399699843568])
    ]),
    CompositeEvaluator([
        CountEvaluator([8.510072290750323, -9.373792682092615]),
        PositionalEvaluator([
            31.971423843574968, 14.6907728523402, -7.685216232429731, 9.117201318326877, 0.579848138955349, 3.528798386363931,
            -38.400120465116224, -9.108009057864122, 4.064907665227836, -10.095780097759146, -5.5954512195441355, -0.4304405886095838
        ]),
        PotentialMobilityEvaluator([-39.24605151185242, 54.88637107718916]),
        ParityEvaluator([-1.3425023100260471])]),
    CompositeEvaluator([
        CountEvaluator([5.957888288553967, -6.416689729843682]),
        PositionalEvaluator([
            17.061290608969088, 12.771163326624006, 0.16011992598971792, 5.256065974262159, -2.7082198004508884, 5.761565061174206,
            -17.609974958421642, -7.990913552944318, -0.17123611973109557, -3.7506276966426806, -10.426285132327546, 4.36665627337486
        ]),
        PotentialMobilityEvaluator([-42.372174303693505, 47.04024691738324]),
        ParityEvaluator([-2.685945015249143])
    ]),
    name='CSTE1'
)

# Pesos ajustados para modo wrap-around
WRAP_AROUND_WIN_TUNED_EVALUATOR = PhaseAwareEvaluator(
    CompositeEvaluator([
        CountEvaluator([-0.11322364220185019, -0.07125739709738235]),
        PositionalEvaluator([
            0.1939658600960192, 0.6870211360693476, -0.3842604740650718, -1.8384465507598533, 0.48418200230890995, 0.5057686589155872,
            -0.41906074571308927, -0.4024262485426815, 1.0473835840618875, -0.4784642924861827, 0.37123155870192415, -0.25032144757134817
        ]),
        PotentialMobilityEvaluator([-0.31255661421348546, -0.12718613669112266]),
        ParityEvaluator([-0.08249842863341596])]),
    CompositeEvaluator([
        CountEvaluator([1.090043119201411, -1.0886657542328209]),
        PositionalEvaluator([
            1.2832409793421167, 2.804994314272912, 0.3838338780900965, 0.0620560136737736, 1.09422798772852, 0.22075658402999657,
            -0.6250644097260232, -3.4809848746456478, 0.3468909941672993, -2.181648617103424, 0.6992049486816784, 0.4070387135981507
        ]),
        PotentialMobilityEvaluator([-6.072244744253591, 5.09481679243193]),
        ParityEvaluator([-0.973793928593382])
    ]),
    CompositeEvaluator([
        CountEvaluator([2.328426262249328, -1.8063665892139995]),
        PositionalEvaluator([
            0.9239504286382842, 4.36128601224762, 1.1169776173719634, 2.202190174091461, 2.6303842456279787, 0.5271874502997308,
            0.22397994186715087, -4.2225920496299, -1.309341399723787, -4.209117002687378, 0.8683085927991591, -0.04513692603300287
        ]),
        PotentialMobilityEvaluator([-13.685981428380908, 9.882144566292695]),
        ParityEvaluator([-1.6388962867283068])
    ]),
    name='WWTE1'
)

WRAP_AROUND_SCORE_TUNED_EVALUATOR = PhaseAwareEvaluator(
    CompositeEvaluator([
        CountEvaluator([3.2056012891108954, 1.5778229320004669]),
        PositionalEvaluator([
            4.124420718347344, 11.082726547006386, -0.8131988362877118, -8.458847789853428, 7.672213758840715, 4.947004687948939,
            -3.4520826604704022, 1.2087190538279342, 9.343978687596378, -3.7703511448367286, 5.718316556797465, 1.9951414292988934
        ]),
        PotentialMobilityEvaluator([-35.048740935696074, -15.623933578915748]), 
        ParityEvaluator([0.7118897608586245])]),
    CompositeEvaluator([
        CountEvaluator([8.400360800656559, -7.65539345993789]),
        PositionalEvaluator([
            6.680615696144641, 24.175719488961033, 2.719775735799597, -0.5986465589582202, 8.764561532278703, 1.5195868494020133,
            -6.850934446508389, -24.662232026932877, 1.5317545552272798, -11.101276431162558, 2.991005475203684, 1.9656447176205263
        ]),
        PotentialMobilityEvaluator([-43.75689241761439, 36.537313671317776]),
        ParityEvaluator([-6.406817210748426])
    ]),
    CompositeEvaluator([
        CountEvaluator([7.953456951079849, -6.345038292345692]),
        PositionalEvaluator([
            1.9662922920880646, 15.46628370655382, 2.8595238210594145, 7.505742152364171, 9.113593519426967, 2.584057689882304,
            -1.8697602216446227, -15.643283797024985, -3.5223861823749814, -14.453482049215664, 3.7410772448266947, 0.9981789757347982
        ]),
        PotentialMobilityEvaluator([-35.87545565876322, 26.141403368596205]),
        ParityEvaluator([-6.582108767528246])
    ]),
    name='WSTE1'
)
