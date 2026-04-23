import os
import argparse
import pathlib
import tqdm
import tqdm.contrib.concurrent
import pickle

from match import *

class Study:
    matches: list[Match]
    
    def __init__(self, matches: list[Match] | None = None):
        if matches is None:
            matches = []
        
        self.matches = matches
    
    def append(self, match: Match):
        self.matches.append(match)
    
    def extend(self, study: Self):
        self.matches.extend(study)
    
    def save(self, path: pathlib.Path):
        with open(path, 'wb') as f:
            pickle.dump(self.matches, f)
    
    def __len__(self):
        return len(self.matches)
    
    def __iter__(self):
        return iter(self.matches)

    @staticmethod
    def load(path: pathlib.Path) -> 'Study':
        if path.is_dir():
            study = Study()
            
            for file in path.iterdir():
                if file.suffix == '.pkl':
                    study.extend(Study.load(file))
            
        with open(path, 'rb') as f:
            return pickle.load(f)

def setup_study_command(parser: argparse.ArgumentParser):
    parser.add_argument('--workers', '-w', type=int, default=8)
    parser.add_argument('--output', '-o', type=pathlib.Path, default=pathlib.Path('studies'))
    parser.set_defaults(func=execute_study)
    
    subparsers = parser.add_subparsers(dest='generator', required=True)
    
    minimax_depths = list(range(1, 11))

    classical_depth_sweep_1_to_10_parser = subparsers.add_parser('classical_depth_sweep_1_to_10')
    classical_depth_sweep_1_to_10_parser.set_defaults(gen=lambda _: generate_depth_sweep(ClassicalGameVariant(), range(9, 12), 2))  
    
    classical_random_mcts_parser = subparsers.add_parser('classical_random_mcts')
    classical_random_mcts_parser.set_defaults(gen=lambda _: generate_tournament(ClassicalGameVariant(), RandomAgent(), MCTSAgent(1000), 50))

def simulate_match(match: Match):
    match.play()

    return match

def execute_study(args: Any):
    workers = args.workers
    output = args.output
    
    
    if output.is_dir():
        output = output / f'{args.generator}.pkl'
    
    matches = args.gen(args)
    matches = tqdm.contrib.concurrent.process_map(simulate_match, matches, max_workers=workers)
    
    study = Study(matches)
    
    study.save(output)
    
def generate_depth_sweep(variant: GameVariant, depths: Iterable[int], n: int = 50):
    matches: list[Match] = []
    
    for depth in depths:
        agent_one = MinimaxAgent(AdvancedPhaseAwareEvaluator(), depth)
        agent_two = MCTSAgent(1000)
        
        matches.extend(generate_tournament(variant, agent_one, agent_two, n))
        
    return matches
    
def generate_tournament(variant: GameVariant, agent_one: Agent, agent_two: Agent, n: int):
    matches: list[Match] = []
    
    for _ in range(n):
        matches.append(Match(variant, agent_one, agent_two))
        
    for _ in range(n):
        matches.append(Match(variant, agent_two, agent_one))
    
    return matches
