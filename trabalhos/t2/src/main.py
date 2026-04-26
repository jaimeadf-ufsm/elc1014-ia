import sys
import argparse
import pathlib

from game import *
from agent import *
from match import *

def add_view_command(view_parser: argparse.ArgumentParser):
    from commands.view import view
    
    view_parser.set_defaults(func=view)

def add_simulate_commands(parser: argparse.ArgumentParser):
    from commands.simulate import SIMULATE_VARIANTS, SIMULATE_PRESETS, simulate
    
    parser.add_argument('--matches', '-n', type=int, default=50)
    parser.add_argument('--workers', '-w', type=int, default=8)
    parser.add_argument('--output', '-o', type=pathlib.Path, default=pathlib.Path('simulations'))
    parser.add_argument('variant', choices=SIMULATE_VARIANTS.keys())
    parser.add_argument('preset', choices=SIMULATE_PRESETS.keys())
    parser.set_defaults(func=simulate)
    
def add_learn_command(parser: argparse.ArgumentParser):
    from commands.learn import LEARN_GOALS, learn
    
    parser.add_argument('--iterations', '-i', type=int, default=10000)
    parser.add_argument('input', type=pathlib.Path)
    parser.add_argument('goal', choices=LEARN_GOALS.keys())
    parser.set_defaults(func=learn)

def add_analyze_command(parser: argparse.ArgumentParser):
    from commands.analyze import ANALYZE_PIPELINES, analyze
    
    parser.add_argument('--output', '-o', type=pathlib.Path, default=pathlib.Path('analysis'))
    parser.add_argument('input', type=pathlib.Path)
    parser.add_argument('pipeline', choices=ANALYZE_PIPELINES.keys())
    parser.set_defaults(func=analyze)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    add_view_command(subparsers.add_parser('view'))
    add_simulate_commands(subparsers.add_parser('simulate'))
    add_learn_command(subparsers.add_parser('learn'))

    if '__pypy__' not in sys.builtin_module_names:
        add_analyze_command(subparsers.add_parser('analyze'))
  
    args = parser.parse_args()
    args.func(args)
    