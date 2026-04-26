import random
import tqdm
import tqdm.contrib.concurrent

from study import *
    
def play_match(match: Match):
    match.play()
    return match

def generate_randomized_matchups(variant: GameVariant, agent_one: Agent, agent_two: Agent, n: int, steps: tuple[int, int] = (0, 8)):
    matches = generate_matchup(variant, agent_one, agent_two, n)
    
    for match in matches:
        state = variant.create_game()
        
        for _ in range(random.randint(*steps)):
            if state.is_over():
                state = variant.create_game()
            
            move = random.choice(state.moves)
            state = variant.make_move(state, move)
            
        match.restart(state)
        
        yield match
            
def generate_matchup(variant: GameVariant, agent_one: Agent, agent_two: Agent, n: int):
    for _ in range(n):
        yield Match(variant, agent_one, agent_two)
        
    for _ in range(n):
        yield Match(variant, agent_two, agent_one)

SIMULATE_VARIANTS = {
    'classical': ClassicalGameVariant(),
    'wrap_around': WrapAroundGameVariant()
}

SIMULATE_PRESETS = {
    'randomized_mcts_1000_vs_mcts_1000':(
        lambda variant, matches:
            generate_randomized_matchups(
                variant,
                MCTSAgent(1000),
                MCTSAgent(1000),
                matches
            )
    ),
    'randomized_mcts_5000_vs_mcts_5000':(
        lambda variant, matches:
            generate_randomized_matchups(
                variant,
                MCTSAgent(5000),
                MCTSAgent(5000),
                matches
            )
    ),
    'randomized_mcts_10000_vs_mcts_10000':(
        lambda variant, matches:
            generate_randomized_matchups(
                variant,
                MCTSAgent(10000),
                MCTSAgent(10000),
                matches
            )
    ),
    'randomized_mcts_25000_vs_mcts_25000':(
        lambda variant, matches:
            generate_randomized_matchups(
                variant,
                MCTSAgent(25000),
                MCTSAgent(25000),
                matches
            )
    )
}

for evaluator in [SIMPLE_COUNT_EVALUATOR, CLASSICAL_EMPIRIC_EVALUATOR, CLASSICAL_SCORE_TUNED_EVALUATOR, CLASSICAL_WIN_TUNED_EVALUATOR, WRAP_AROUND_WIN_TUNED_EVALUATOR, WRAP_AROUND_SCORE_TUNED_EVALUATOR]:
    for depth in range(1, 7):
        for iterations in [2500, 5000, 7500, 10000]:
            assert evaluator.name is not None
            SIMULATE_PRESETS[f'standard_minimax_{evaluator.name.lower()}_{depth}_vs_mcts_{iterations}'] = (
                lambda variant, matches, depth=depth, iterations=iterations, evaluator=evaluator:
                    generate_matchup(
                        variant,
                        MinimaxAgent(evaluator, depth),
                        MCTSAgent(iterations),
                        matches
                    )
            )

def simulate(args: Any):
    n = args.matches
    workers = args.workers
    output = args.output
    variant = SIMULATE_VARIANTS[args.variant]
    preset = SIMULATE_PRESETS[args.preset]
    
    if output.is_dir():
        output = output / f'{args.generator}.pkl'
    
    matches = preset(variant, n)
    matches = list(matches)
    
    matches = tqdm.contrib.concurrent.process_map(
        play_match,
        matches,
        max_workers=workers
    )
    
    study = Study(matches)
    
    study.save(output)