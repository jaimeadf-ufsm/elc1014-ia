import time
from typing import Any

from agent import *
from game import *

# Registro de um turno dentro de uma partida.
#
# Guarda a jogada escolhida, o estado resultante após aplicá-la e um conjunto
# de métricas associado à decisão.
class Turn:
    move: Move | None               # Movimento escolhido (pode ser None para estado inicial)
    state: GameState                # estado após aplicar o movimento
    metrics: dict[str, Any]         # Dicionário com dados da decisão (tempo, nós xplorados etc)
    
    # Ex.:
    # Turn(
    #   move=Move(position=(2,3), captures=[...], placements=[...]),
    #   state=GameState(...),  # Estado após o movimento
    #   metrics={
    #     'elapsed_time': 0.052,
    #     'total_nodes_explored': 1245,
    #     'total_nodes_pruned': 890
    #   }
    # )

    def __init__(self, move: Move | None, state: GameState, metrics: dict[str, Any]):
        self.move = move
        self.state = state
        self.metrics = metrics

# Orquestra uma partida entre dois agentes sob uma variante de jogo.
# Ex.:
# match = Match(
#     variant=ClassicalGameVariant(size=6),
#     black_agent=MinimaxAgent(SIMPLE_COUNT_EVALUATOR, depth=4),
#     white_agent=RandomAgent()
# )

# match.history[0] = Turn(None, estado_inicial, {})
# match.history[0].state.player = Player.BLACK  # Pretas começam

class Match:
    variant: GameVariant
    
    history: list[Turn]             # Lista de todos os turnos
    
    black_agent: Agent              # Agente que joga como Pretas
    white_agent: Agent              # Agente que joga como Brancas
    
    def __init__(self, variant: GameVariant, black_agent: Agent, white_agent: Agent):
        self.variant = variant
        self.history = [Turn(None, variant.create_game(), {})]      # Histórico com um único turno, sem métricas
        self.black_agent = black_agent
        self.white_agent = white_agent
    
    # Retorna o último estado (estado atual)
    @property
    def state(self):
        return self.history[-1].state
    
    # Executa um turno
    def turn(self):
        if self.state.is_over():
            return None
        
        # Obtém o agente do jogador cuja vez é
        agent = self.get_player_agent(self.state.player)

        start_time = time.perf_counter()
        move, agent_metrics = agent.get_move(self.variant, self.state)
        end_time = time.perf_counter()

        # Relógio que mede quanto tempo o agente levou para decidir
        elapsed_time = end_time - start_time
        
        if move is not None:
            metrics = {
                **agent_metrics,                        # Desempacota o dicionário do agente
                'elapsed_time': elapsed_time            # Add essa métrica aos dados existentes
            }
            
            # Aplica movimento gerando novo estado
            state = self.variant.make_move(self.state, move)

            # Adiciona o novo estado ao histórico de turnos
            self.history.append(Turn(move, state, metrics))
        
        return move

    # Enquanto o jogo não terminou, executa um turno
    def play(self):
        while not self.state.is_over():
            self.turn()
        
    # Dois casos: ser argumento reinicia normal (jogo do zero), ou então recomeça do estado específico
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
