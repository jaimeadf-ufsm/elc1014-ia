from match import *

def view(args: Any):
    from gui import GUI
    
    provider = InputProvider()
    
    variant = WrapAroundGameVariant(6)

    black_agent = MinimaxAgent(CLASSICAL_SCORE_TUNED_EVALUATOR, 8)
    white_agent = MCTSAgent(10000)
    
    match = Match(variant, black_agent, white_agent)
    
    gui = GUI(match, provider, 'manual')
    
    gui.run()