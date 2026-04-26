from typing import Any
from collections import Counter
import random


from study import *
from evaluator import *

# Regressão logística -> ganhar partidas
def tune_for_win(study: Study, evaluator: Evaluator, iterations: int):
    from sklearn.linear_model import LogisticRegression
    
    X = []
    y = []
    
    for match in study:
        winner = match.state.winner
        
        if winner == None:
            continue
        
        for turn in match.history[:-1]:
            features = evaluator.params(match.variant, turn.state)
            
            X.append(features)
            y.append(winner == Player.WHITE)
    
    X = np.array(X)
    y = np.array(y)
    
    model = LogisticRegression(max_iter=iterations, fit_intercept=False)
    model.fit(X, y)
    
    evaluator.weights(model.coef_[0])

# Regressão linear -> maximizar score
def tune_for_score(study: Study, evaluator: Evaluator, iterations: int):
    from sklearn.linear_model import LinearRegression
    
    X = []
    y = []
    
    for match in study:
        white_pieces = match.state.board.count_pieces(Player.WHITE)
        black_pieces = match.state.board.count_pieces(Player.BLACK)
        
        score = white_pieces - black_pieces
        
        for turn in match.history[:-1]:
            features = evaluator.params(match.variant, turn.state)
            
            X.append(features)
            y.append(score)
    
    X = np.array(X)
    y = np.array(y)
    
    model = LinearRegression(fit_intercept=False)
    model.fit(X, y)
    
    evaluator.weights(model.coef_)
    
LEARN_GOALS = {
    'win': tune_for_win,
    'score': tune_for_score
}

def learn(args: Any):
    input_path = args.input
    iterations = args.iterations
    tune = LEARN_GOALS[args.goal]
    
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
    
    tune(study, evaluator, iterations)
    
    for i, match in enumerate(random.choices(study.matches, k=20)):
        white_pieces = match.state.board.count_pieces(Player.WHITE)
        black_pieces = match.state.board.count_pieces(Player.BLACK)
        
        score = white_pieces - black_pieces
        
        print(f'Match {i + 1}:')
        print(f'  Winner: {match.state.winner}')
        print(f'  Score: W{white_pieces} - B{black_pieces} = {score}')
        print(f'  Turns:')
        
        for j, turn in enumerate(match.history[1:]):
            score = evaluator.evaluate(match.variant, turn.state)
            print(f'    {turn.state.count:02d} {turn.state.player:>6}: {score}')
        
        print()
        
    print(evaluator)