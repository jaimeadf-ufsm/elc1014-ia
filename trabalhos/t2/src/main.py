import argparse

from game import *
from agent import *
from engine import *
from gui import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    provider = InputProvider()
    
    variant = WrapAroundVariant()

    black_agent = MinimaxAgent(SimpleCountEvaluator(), 6)
    white_agent = HumanAgent(provider)
    
    engine = Engine(variant, black_agent, white_agent)
    gui = GUI(engine, provider, 'auto')
    
    gui.run()