import os

class FileINFO:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = os.path.basename(filepath)
        self.cwd = os.path.dirname(filepath)

class MutantFileINFO(FileINFO):
    def __init__(self, path):
        super().__init__(path)
        self.compiler = None    # TODO: Add compiler info
        self.function : dict[str: list[str]] = {}
        self.global_opts : list[str] = []

    def add_func_opts(self, function : str, opts : list[str]):
        self.function[function] = opts

class CaseManager:
    def __init__(self, orig : FileINFO = None):
        self.case_dir = orig.cwd
        self.orig : FileINFO = orig
        self.mutants : list[MutantFileINFO] = []

    def set_orig(self, orig: FileINFO):
        self.orig = orig
        
    def add_mutant(self, mutant: MutantFileINFO):
        self.mutants.append(mutant)