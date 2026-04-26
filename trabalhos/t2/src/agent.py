import random
import math
from typing import Self, Any

from move import *
from game import *
from evaluator import *
from provider import *

# Classe base para agentes que escolhem jogadas.
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

# Agente que escolhe uma jogada legal ao acaso.
#
# Serve como referência simples de desempenho e também como fonte de partidas
# variadas em simulações.
class RandomAgent(Agent):
    def get_move(self, variant: GameVariant, state: GameState):
        return random.choice(state.moves), {}
    
# Agente controlado por humano.
#
# Delega a escolha a um InputProvider (GUI/CLI), bloqueando até que alguém
# informe a jogada. Isso permite que a mesma infraestrutura de partida seja
# usada de forma interativa.
class HumanAgent(Agent):
    provider: InputProvider
    
    def __init__(self, provider: InputProvider):
        self.provider = provider
    
    def get_move(self, variant: GameVariant, state: GameState):
        return self.provider.request_move(variant, state), {}

# Agente minimax com poda alfa-beta.
#
# Explora a árvore de jogo até uma profundidade fixa e usa um Evaluator para
# pontuar estados folha. Como os avaliadores do projeto são definidos do ponto
# de vista das brancas, este agente trata:
#   - brancas como jogador maximizador;
#   - pretas como jogador minimizador.
#
# Além do movimento escolhido, retorna métricas da busca (nós explorados e
# podados por profundidade), úteis para comparar configurações e agentes.
class MinimaxAgent(Agent):
    evaluator: Evaluator
    depth: int
    
    def __init__(self, evaluator: Evaluator, depth: int):
        self.evaluator = evaluator
        self.depth = depth
        
    def get_move(self, variant: GameVariant, state: GameState):
        # Dicionário de métricas, para cada profundidade d salva quantidade de nós
        # explorados e nós podados
        metrics: dict[str, Any] = {
            'by_depth': { d: { 'nodes_explored': 0, 'nodes_pruned': 0 } for d in range(0, self.depth + 1) }
        }
        
        score, move = self.minimax(variant, state, self.depth, float('-inf'), float('inf'), metrics)
        assert move is not None
        
        # Atualiza as métricas totais
        metrics['total_nodes_explored'] = sum(depth_metrics['nodes_explored'] for depth_metrics in metrics['by_depth'].values())
        metrics['total_nodes_pruned'] = sum(depth_metrics['nodes_pruned'] for depth_metrics in metrics['by_depth'].values())
        
        return move, metrics
        
    def minimax(self, variant: GameVariant, state: GameState, depth: int, alpha: float, beta: float, metrics: dict[str, Any]):
        # Caso base
        if depth == 0 or state.is_over():
            return self.evaluator.evaluate(variant, state), None
        
        # Se for Brancas, maximiza, caso contrário minimiza
        maximizing = state.player == Player.WHITE
        
        # Brancas
        if maximizing:
            max_score = float('-inf')
            max_move = None
            
            # Itera sobre os possíveis movimentos no estado atual
            for i, move in enumerate(state.moves):
                # Para cada estado explorado, incrementa a métrica
                metrics['by_depth'][self.depth - depth]['nodes_explored'] += 1

                # Busca o próximo estado, reduzindo a profundidade
                next_state = variant.make_move(state, move)
                next_score, _ = self.minimax(variant, next_state, depth - 1, alpha, beta, metrics)
                
                # Atualiza se encontrou melhor score
                if next_score >= max_score:
                    max_score = next_score
                    max_move = move

                    alpha = max(alpha, max_score)                    
                    
                # Poda e conta quantos nós foram podados
                if beta <= alpha:
                    metrics['by_depth'][self.depth - depth]['nodes_pruned'] += len(state.moves) - i - 1
                    break
            
            return max_score, max_move
        # Pretas
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
    
    # Dois agentes minimax são iguais se têm o mesmo evaluator e depth
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MinimaxAgent):
            return False
        
        return self.evaluator == value.evaluator and self.depth == value.depth
    
    # Baseado na classe, evaluator e depth
    def __hash__(self) -> int:
        return hash((self.__class__, self.evaluator, self.depth))
    
    # MinimaxAgente(evaluator=..., depth=4)
    def __str__(self) -> str:
        return f'{self.__class__.__name__}(evaluator={self.evaluator}, depth={self.depth})'
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(evaluator={repr(self.evaluator)}, depth={self.depth})'

# Nó de busca do Monte Carlo Tree Search (MCTS).
#
# Cada nó guarda um estado do jogo associado a uma jogada (move) e mantém
# estatísticas acumuladas ao longo das simulações:
#   - n: número de visitas;
#   - q: valor acumulado, atualizado na retropropagação a partir do resultado
#        do rollout, do ponto de vista do jogador que realizou a jogada que
#        leva a este nó (ou seja, o jogador do estado do pai).
#
# Também encapsula as operações centrais do algoritmo:
#   - expansão de um movimento ainda não tentado;
#   - simulação (rollout) até o fim da partida;
#   - seleção de filhos via UCT.
class MCTSNode:
    state: GameState                # Estado do jogo neste nó
    variant: GameVariant            # Regras do jogo
    
    move: Move | None               # Jogada que levou a este nó

    n: int                          # Número de visitas (o quanto de evidência temos)
    q: float                        # Valor acumulado (o quão bom tem sido esse nó)

    parent: Self | None             # Nó pai
    children: list['MCTSNode']      # Filhos já expandidos
    
    untried_moves: list[Move]       # Movimentos ainda não explorados
    
    def __init__(self, variant: GameVariant, state: GameState, move: Move | None, parent: Self | None):
        self.variant = variant
        self.state = state
        
        self.move = move
        
        self.n = 0
        self.q = 0.0
        
        self.parent = parent
        self.children = []
        
        self.untried_moves = state.moves.copy()     # Copia todos os movs legais

    def expand(self):
        next_move = self.untried_moves.pop()        # Remove e retorna último movimento não tentado
        
        next_state = self.variant.make_move(self.state, next_move)
        next_node = MCTSNode(self.variant, next_state, next_move, self)
        
        self.children.append(next_node)
        
        return next_node
    
    # Simulação aleatória a partir do estado até o fim do jogo, retorna vencedor
    def rollout(self):
        state = self.state
        
        while not state.is_over():
            move = self.rollout_policy(state)
            state = self.variant.make_move(state, move)
        
        return state.winner

    # Política: movimento aleatório
    def rollout_policy(self, state: GameState):
        return random.choice(state.moves)

    # Atualiza estatísitcas na árvore, q acumula pontos do ponto de vista do jogador
    # que fez o movimento (de quem era a vez no pai)
    def backpropagate(self, result: Player | None):
        self.n += 1     # Incrementa visitas deste nó
        
        if self.parent:
            if result == self.parent.state.player:
                self.q += 1     # Vitória do jogador que veio para cá
            elif result == self.parent.state.player.opponent():
                self.q -= 1     # Derrota
            
            self.parent.backpropagate(result)
    
    # UCT, c padrão = 1.4
    def best_child(self, c):
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
            
# Agente baseado em Monte Carlo Tree Search (MCTS) com seleção UCT.
#
# Executa um número fixo de iterações (seleção/expansão/rollout/
# retropropagação) a partir do estado atual e escolhe a jogada do filho mais
# promissor na raiz (explotação no final).
#
# Retorna também métricas agregadas da busca para apoiar análises.
class MCTSAgent(Agent):
    iterations: int     # Quantas iterações MCTS executar
    c: float = 1.4      # Parâmetro UCT
    
    def __init__(self, iterations: int, c: float = 1.4):
        self.iterations = iterations
        self.c = c
        
    def get_move(self, variant: GameVariant, state: GameState):
        root = MCTSNode(variant, state, None, None)     # Cria raiz no estado atual
        
        for i in range(self.iterations):
            leaf = self.tree_policy(root)       # Fase 1: seleção + expansão
            result = leaf.rollout()             # Fase 2: simulação
            leaf.backpropagate(result)          # Fase 3: retropropagação
            
        metrics = {
            'total_nodes_explored': root.n,
        }
            
        return root.best_child(0).move, metrics     # Retorna movimento do melhor filho
    
    # Desce pela árvore usando UCT, ao encontrar nó não totalmente expandido, expande um filho
    # Se chegar num terminal, retorna ele
    def tree_policy(self, root: MCTSNode):
        node = root
        
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node.expand()            # Expande novo nó
            else:
                node = node.best_child(self.c)  # Desce pela melhor rota
        
        return node     # Retorna folha para rollout
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MCTSAgent):
            return False
        
        return self.iterations == value.iterations and self.c == value.c
    
    def __hash__(self) -> int:
        return hash((self.__class__, self.iterations, self.c))
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}(iterations={self.iterations}, c={self.c})'
    