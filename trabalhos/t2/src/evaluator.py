from game import *

"""
EVALUATORS DISPONÍVEIS - ESTRATÉGIAS POR FASE DO JOGO

1. SimpleCountEvaluator (baseline)
   - Apenas conta diferença de peças
   - Útil como baseline para comparação

2. PositionalEvaluator
   - Avalia a importância de cada posição no tabuleiro
   - Valores das casas:
     * Cantos: +100 (posições mais valiosas)
     * X-squares (diagonais dos cantos): -50 (perigosas)
     * C-squares (adjacentes aos X-squares): -25 (perigosas)
     * Bordas: +10 (seguras, boas)
     * Centro: +5 (controle importante)
     * Outras: +1

3. QuietMoveEvaluator
   - Prioriza jogadas "silenciosas" (com poucas capturas)
   - Combina avaliação posicional com penalidade para muitos movimentos
   - Útil para abertura e meio-jogo

4. PhaseAwareEvaluator (RECOMENDADO)
   - Adapta estratégia conforme fase:
     * ABERTURA (≤30 peças): 60% posição + 40% contagem
     * MEADO (30-50 peças): 40% posição + 60% contagem
     * FINAL (≥50 peças): 80% contagem + 20% posição
   - Simples e efetivo

5. AdvancedPhaseAwareEvaluator (MAIS SOFISTICADO)
   - Versão avançada com métricas adicionais:
     * Avaliação posicional
     * Contagem de peças
     * Mobilidade (número de movimentos disponíveis)
     * Segurança nas bordas (penaliza X e C-squares do oponente)
   - Pesos variam por fase para comportamento adaptativo
"""

class Evaluator:
    @abstractmethod
    def evaluate(self, variant: GameVariant, state: GameState, player: Player) -> float:
        pass
    
    def __eq__(self, value: object) -> bool:
        return isinstance(value, self.__class__)
    
    def __hash__(self) -> int:
        return hash(self.__class__)
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}()'

class SimpleCountEvaluator(Evaluator):
    def evaluate(self, variant: GameVariant, state: GameState, player: Player):
        black_pieces = state.board.count_pieces(Player.BLACK)
        white_pieces = state.board.count_pieces(Player.WHITE)
        
        if player == Player.BLACK:
            return black_pieces - white_pieces
        else:
            return white_pieces - black_pieces
    
class PositionalEvaluator(Evaluator):
    """Avalia baseado no valor das posições no tabuleiro."""
    
    def __init__(self, board_size: int = 8):
        self.board_size = board_size
        # Matriz de valores para posições (padrão Othello)
        self.position_values = self._create_position_matrix(board_size)
    
    def _create_position_matrix(self, size: int) -> list[list[int]]:
        """Cria matriz de valores para posições:
        +100 cantos
        -50 X-squares (diagonais dos cantos)
        -25 C-squares (ao lado dos X-squares)
        +5 centro
        +10 bordas
        """
        matrix = [[0] * size for _ in range(size)]
        
        for row in range(size):
            for col in range(size):
                # Cantos
                if (row == 0 or row == size - 1) and (col == 0 or col == size - 1):
                    matrix[row][col] = 100
                # X-squares (diagonal dos cantos)
                elif (row in [1, size - 2] and col in [1, size - 2]):
                    matrix[row][col] = -50
                # C-squares (ao lado dos X-squares)
                elif ((row in [0, size - 1] and col in [1, size - 2]) or
                      (row in [1, size - 2] and col in [0, size - 1])):
                    matrix[row][col] = -25
                # Bordas (não cantos, X ou C)
                elif row == 0 or row == size - 1 or col == 0 or col == size - 1:
                    matrix[row][col] = 10
                # Centro (4 casas centrais)
                elif (row in [size // 2 - 1, size // 2] and 
                      col in [size // 2 - 1, size // 2]):
                    matrix[row][col] = 5
                else:
                    matrix[row][col] = 1
        
        return matrix
    
    def evaluate(self, variant: GameVariant, state: GameState, player: Player) -> float:
        """Avalia o estado baseado no valor das posições."""
        score = 0
        opponent = player.opponent()
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                piece = state.board[row, col]
                value = self.position_values[row][col]
                
                if piece == player:
                    score += value
                elif piece == opponent:
                    score -= value
        
        return score


class QuietMoveEvaluator(Evaluator):
    """Prioriza jogadas que capturam poucas peças (jogadas silenciosas)."""
    
    def __init__(self, board_size: int = 8):
        self.board_size = board_size
        self.positional = PositionalEvaluator(board_size)
    
    def evaluate(self, variant: GameVariant, state: GameState, player: Player) -> float:
        """Avalia priorizando jogadas com poucas capturas."""
        # Score posicional base
        positional_score = self.positional.evaluate(variant, state, player)
        
        # Penalidade se há muitos capturas possíveis (indica agressividade)
        # Jogadas silenciosas têm poucas capturas
        quiet_bonus = -len(state.moves) * 0.5
        
        return positional_score + quiet_bonus


class PhaseAwareEvaluator(Evaluator):
    """Adapta a estratégia conforme a fase do jogo."""
    
    def __init__(self, board_size: int = 8):
        self.board_size = board_size
        self.positional = PositionalEvaluator(board_size)
        self.simple = SimpleCountEvaluator()
    
    def _get_game_phase(self, state: GameState) -> str:
        """Determina a fase do jogo baseado no número de peças."""
        total_pieces = state.board.count_pieces(Player.BLACK) + state.board.count_pieces(Player.WHITE)
        
        # Início: até 30 peças (primeiras ~15 jogadas)
        if total_pieces <= 30:
            return "opening"
        # Fim: mais de 50 peças (últimas ~15 jogadas)
        elif total_pieces >= 50:
            return "endgame"
        # Meio: entre
        else:
            return "midgame"
    
    def evaluate(self, variant: GameVariant, state: GameState, player: Player) -> float:
        phase = self._get_game_phase(state)
        
        if phase == "opening":
            # Início: Prioriza jogadas silenciosas + controle do centro
            return self._evaluate_opening(variant, state, player)
        elif phase == "midgame":
            # Meio: Continua priorizando jogadas silenciosas
            return self._evaluate_midgame(variant, state, player)
        else:  # endgame
            # Fim: Maximiza número de peças
            return self._evaluate_endgame(variant, state, player)
    
    def _evaluate_opening(self, variant: GameVariant, state: GameState, player: Player) -> float:
        """Fase de abertura: jogadas silenciosas + controle do centro."""
        positional_score = self.positional.evaluate(variant, state, player)
        piece_count = state.board.count_pieces(player) - state.board.count_pieces(player.opponent())
        
        # Pesos: posicional (60%) + contagem de peças (40%)
        return positional_score * 0.6 + piece_count * 0.4
    
    def _evaluate_midgame(self, variant: GameVariant, state: GameState, player: Player) -> float:
        """Fase intermediária: jogadas silenciosas com menos peso no centro."""
        positional_score = self.positional.evaluate(variant, state, player)
        piece_count = state.board.count_pieces(player) - state.board.count_pieces(player.opponent())
        
        # Pesos: posicional (40%) + contagem de peças (60%)
        return positional_score * 0.4 + piece_count * 0.6
    
    def _evaluate_endgame(self, variant: GameVariant, state: GameState, player: Player) -> float:
        """Fase final: maximiza número de peças."""
        piece_count = state.board.count_pieces(player) - state.board.count_pieces(player.opponent())
        positional_score = self.positional.evaluate(variant, state, player)
        
        # Pesos: contagem (80%) + posicional (20%)
        return piece_count * 0.8 + positional_score * 0.2


class AdvancedPhaseAwareEvaluator(Evaluator):
    """Versão avançada com avaliação mais sofisticada de movimentos."""
    
    def __init__(self, board_size: int = 8):
        self.board_size = board_size
        self.position_values = self._create_position_matrix(board_size)
    
    def _create_position_matrix(self, size: int) -> list[list[int]]:
        """Cria matriz de valores para posições."""
        matrix = [[0] * size for _ in range(size)]
        
        for row in range(size):
            for col in range(size):
                if (row == 0 or row == size - 1) and (col == 0 or col == size - 1):
                    matrix[row][col] = 100  # Cantos
                elif (row in [1, size - 2] and col in [1, size - 2]):
                    matrix[row][col] = -50  # X-squares
                elif ((row in [0, size - 1] and col in [1, size - 2]) or
                      (row in [1, size - 2] and col in [0, size - 1])):
                    matrix[row][col] = -25  # C-squares
                elif row == 0 or row == size - 1 or col == 0 or col == size - 1:
                    matrix[row][col] = 10  # Bordas
                elif (row in [size // 2 - 1, size // 2] and 
                      col in [size // 2 - 1, size // 2]):
                    matrix[row][col] = 5  # Centro
                else:
                    matrix[row][col] = 1
        
        return matrix
    
    def _get_game_phase(self, state: GameState) -> str:
        """Determina a fase do jogo."""
        total_pieces = state.board.count_pieces(Player.BLACK) + state.board.count_pieces(Player.WHITE)
        
        if total_pieces <= 30:
            return "opening"
        elif total_pieces >= 50:
            return "endgame"
        else:
            return "midgame"
    
    def _positional_score(self, state: GameState, player: Player) -> float:
        """Calcula score posicional."""
        score = 0
        opponent = player.opponent()
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                piece = state.board[row, col]
                value = self.position_values[row][col]
                
                if piece == player:
                    score += value
                elif piece == opponent:
                    score -= value
        
        return score
    
    def _piece_count(self, state: GameState, player: Player) -> float:
        """Calcula diferença de peças."""
        return state.board.count_pieces(player) - state.board.count_pieces(player.opponent())
    
    def _mobility_score(self, state: GameState, player: Player) -> float:
        """Avalia mobilidade (número de movimentos disponíveis)."""
        # Quanto mais movimentos, melhor (mais opções)
        return len(state.moves)
    
    def _edge_safety(self, state: GameState, player: Player) -> float:
        """Avalia segurança nas bordas (penaliza peças nas X e C squares)."""
        opponent = player.opponent()
        safety_score = 0
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                piece = state.board[row, col]
                
                # Penaliza se oponente tem peças em X ou C squares
                if piece == opponent:
                    if (row in [1, self.board_size - 2] and col in [1, self.board_size - 2]):
                        safety_score -= 50  # X-square
                    elif ((row in [0, self.board_size - 1] and col in [1, self.board_size - 2]) or
                          (row in [1, self.board_size - 2] and col in [0, self.board_size - 1])):
                        safety_score -= 25  # C-square
        
        return safety_score
    
    def evaluate(self, variant: GameVariant, state: GameState, player: Player) -> float:
        phase = self._get_game_phase(state)
        
        positional = self._positional_score(state, player)
        piece_count = self._piece_count(state, player)
        mobility = self._mobility_score(state, player)
        edge_safety = self._edge_safety(state, player)
        
        if phase == "opening":
            # Abertura: equilibra tudo, com foco em controle
            return (positional * 0.4 + 
                    piece_count * 0.2 + 
                    mobility * 0.2 + 
                    edge_safety * 0.2)
        
        elif phase == "midgame":
            # Meio: começa a priorizar contagem, mas mantém posição
            return (positional * 0.3 + 
                    piece_count * 0.4 + 
                    mobility * 0.2 + 
                    edge_safety * 0.1)
        
        else:  # endgame
            # Final: maximize contagem de peças
            return (piece_count * 0.7 + 
                    positional * 0.2 + 
                    mobility * 0.1)