import pickle
import pathlib

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
