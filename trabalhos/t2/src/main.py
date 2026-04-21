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

    # black_agent = MinimaxAgent(SimpleCountEvaluator(), 6)
    black_agent = MCTSAgent(1000)
    white_agent = MinimaxAgent(SimpleCountEvaluator(), 6)
    # white_agent = RandomAgent()
    
    engine = Engine(variant, black_agent, white_agent)
    gui = GUI(engine, provider, 'auto')
    
    gui.run()