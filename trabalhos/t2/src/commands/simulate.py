import random
import tqdm
import tqdm.contrib.concurrent

from study import *
    
def play_match(match: Match):
    match.play()

    return match
    
def generate_matchups_across_minimax_depth(variant: GameVariant, opponent: MCTSAgent, evaluator: Evaluator, depths: Iterable[int], n: int = 50):
    for depth in depths:
        agent_one = MinimaxAgent(evaluator, depth)
        agent_two = opponent
        
        matches = generate_matchup(variant, agent_one, agent_two, n)
        
        for match in matches:
            yield match

def generate_randomized_matchups(variant: GameVariant, agent_one: Agent, agent_two: Agent, n: int):
    matches = generate_matchup(variant, agent_one, agent_two, n)
    
    for match in matches:
        state = variant.create_game()
        
        for _ in range(random.randint(4, 6)):
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

SIMULATE_GENERATORS = {
    'randomized_mcts_1000_vs_mcts_1000':(
        lambda variant, matches:
            generate_randomized_matchups(
                variant,
                MCTSAgent(1000),
                MCTSAgent(1000),
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
    )
}

def simulate(args: Any):
    n = args.matches
    workers = args.workers
    output = args.output
    variant = SIMULATE_VARIANTS[args.variant]
    generator = SIMULATE_GENERATORS[args.generator]
    
    if output.is_dir():
        output = output / f'{args.generator}.pkl'
    
    matches = generator(variant, n)
    matches = list(matches)
    
    matches = tqdm.contrib.concurrent.process_map(play_match, matches, max_workers=workers)
    
    study = Study(matches)
    
    study.save(output)