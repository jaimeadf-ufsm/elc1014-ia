import argparse

from game import *
from agent import *
from engine import *
from gui import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    provider = InputProvider()
    
    variant = ClassicalGameVariant(6)

    # Exemplos de uso dos diferentes evaluators:
    
    # 1. SimpleCountEvaluator - apenas conta peças (baseline)
    black_agent = MinimaxAgent(SimpleCountEvaluator(), 6)
    
    # 2. PositionalEvaluator - avalia posições no tabuleiro
    #black_agent = MinimaxAgent(PositionalEvaluator(), 6)
    
    # 3. QuietMoveEvaluator - prioriza jogadas silenciosas
    #black_agent = MinimaxAgent(QuietMoveEvaluator(), 6)
    
    # 4. PhaseAwareEvaluator - adapta estratégia por fase do jogo
    #black_agent = MinimaxAgent(PhaseAwareEvaluator(), 6)
    
    # 5. AdvancedPhaseAwareEvaluator - versão avançada com múltiplas métricas
    #black_agent = MinimaxAgent(AdvancedPhaseAwareEvaluator(), 6)
    
    #black_agent = MCTSAgent(1000)
    white_agent = MinimaxAgent(SimpleCountEvaluator(), 6)
    # white_agent = RandomAgent()
    
    engine = Engine(variant, black_agent, white_agent)
    gui = GUI(engine, provider, 'auto')
    
    gui.run()