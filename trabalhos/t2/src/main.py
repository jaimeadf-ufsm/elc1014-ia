import argparse
import psutil

from game import *
from agent import *
from match import *

from commands.view import *
from commands.simulate import *
from commands.analyze import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    view_parser = subparsers.add_parser('view')
    view_parser.set_defaults(func=view)
    
    simulate_parser = subparsers.add_parser('simulate')
    simulate_parser.add_argument('--matches', '-n', type=int, default=50)
    simulate_parser.add_argument('--workers', '-w', type=int, default=psutil.cpu_count(logical=False))
    simulate_parser.add_argument('--output', '-o', type=pathlib.Path, default=pathlib.Path('simulations'))
    simulate_parser.add_argument('variant', choices=SIMULATE_VARIANTS.keys())
    simulate_parser.add_argument('generator', choices=SIMULATE_GENERATORS.keys())
    simulate_parser.set_defaults(func=simulate)
    
    analyze_parser = subparsers.add_parser('analyze')
    analyze_parser.add_argument('--output', '-o', type=pathlib.Path, default=pathlib.Path('analysis'))
    analyze_parser.add_argument('input', type=pathlib.Path)
    analyze_parser.add_argument('pipeline', choices=ANALYZE_PIPELINES.keys())
    analyze_parser.set_defaults(func=analyze)
  
    args = parser.parse_args()
    args.func(args)
    