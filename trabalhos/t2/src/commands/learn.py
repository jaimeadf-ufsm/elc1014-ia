from typing import Any
from collections import Counter
import random

from study import *
from evaluator import *

def learn(args: Any):
    from sklearn.linear_model import LogisticRegression
    
    input_path = args.input
    iterations = args.iterations
    
    study = Study.load(input_path)
    
    evaluator = PhaseAwareEvaluator(
        opening=CompositeEvaluator([
            CountEvaluator(),
            PositionalEvaluator(),
            PotentialMobilityEvaluator(),
            ParityEvaluator()
        ]),
        midgame=CompositeEvaluator([
            CountEvaluator(),
            PositionalEvaluator(),
            PotentialMobilityEvaluator(),
            ParityEvaluator()
        ]),
        endgame=CompositeEvaluator([
            CountEvaluator(),
            PositionalEvaluator(),
            PotentialMobilityEvaluator(),
            ParityEvaluator()
        ])
    )
    
    X = []
    y = []
    
    for match in study:
        winner = match.state.winner
        
        if winner == None:
            continue
        
        for turn in match.history[:-1]:
            for player in (Player.BLACK,):
                features = evaluator.params(match.variant, turn.state, player)
                
                X.append(features)
                y.append(classify_outcome(winner, player))
    
    print(f'Collected {len(X)} training samples')
    print('Class distribution:', Counter(y))
            
    X = np.array(X)
    y = np.array(y)
    
    model = LogisticRegression(max_iter=iterations, fit_intercept=False)
    model.fit(X, y)
    
    print('Learned coefficients:', model.coef_)
    print('Learned intercept:', model.intercept_)
    
    evaluator.weights(model.coef_[0])
    
    for i, match in enumerate(random.choices(study.matches, k=20)):
        print(f'Match {i + 1}:')
        print(f'  Winner: {match.state.winner}')
        print(f'  Score: {match.state.board.count_pieces(Player.BLACK)} - {match.state.board.count_pieces(Player.WHITE)}')
        print(f'  Turns:')
        
        for j, turn in enumerate(match.history[1:]):
            player = match.history[j].state.player
            
            black_score = evaluator.evaluate(match.variant, turn.state, Player.BLACK)
            white_score = evaluator.evaluate(match.variant, turn.state, Player.WHITE)
            
            black_score = 1 / (1 + np.exp(-black_score))
            white_score = 1 / (1 + np.exp(-white_score))
            
            print(f'    {turn.state.count:02d} {turn.state.player:>6}: B: {black_score:.4f}, W: {white_score:.4f}')
        
        print()
        
    print(evaluator)

def classify_outcome(winner: Player | None, player: Player):
    if winner is None:
        return 0
    elif winner == player:
        return 1
    else:
        return -1
