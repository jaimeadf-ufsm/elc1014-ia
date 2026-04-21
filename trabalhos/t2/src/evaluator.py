from game import *

class Evaluator:
    @abstractmethod
    def evaluate(self, variant: GameVariant, state: GameState, player: Player) -> float:
        pass

class SimpleCountEvaluator(Evaluator):
    def evaluate(self, variant: GameVariant, state: GameState, player: Player):
        black_pieces = state.board.count_pieces(Player.BLACK)
        white_pieces = state.board.count_pieces(Player.WHITE)
        
        if player == Player.BLACK:
            return black_pieces - white_pieces
        else:
            return white_pieces - black_pieces