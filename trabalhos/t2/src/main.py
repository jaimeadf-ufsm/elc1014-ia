import argparse

from game import *
from agent import *
from match import *
from gui import *
from study import *
from analysis import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    setup_gui_command(subparsers.add_parser('gui'))
    setup_study_command(subparsers.add_parser('study'))
    setup_analysis_command(subparsers.add_parser('analysis'))
  
    args = parser.parse_args()
    args.func(args)
    