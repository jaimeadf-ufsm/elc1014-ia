from match import *

def view(args: Any):
    from gui import GUI
    
    provider = InputProvider()
    
    variant = ClassicalGameVariant(6)

    black_agent = MinimaxAgent(DIEGO_EVALUATOR, 7)
    white_agent = MCTSAgent(1000)
    
    match = Match(variant, black_agent, white_agent)
    
    gui = GUI(match, provider, 'manual')
    
    gui.run()