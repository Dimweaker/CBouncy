import os

class FileINFO:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = os.path.basename(filepath)
        self.cwd = os.path.dirname(filepath)

class MutantFileINFO(FileINFO):
    def __init__(self, path: str, function : dict[str: list[str]] = None):
        super().__init__(path)
        self.compiler = None    # TODO: Add compiler info
        if function is not None:
            self.function = function
        else:
            self.function : dict[str: list[str]] = dict()

    def add_func_opts(self, function : str, opts : list[str]):
        self.function[function] = opts

class CaseManager:
    def __init__(self, orig : FileINFO = None):
        self.case_dir = orig.cwd
        self.orig : FileINFO = orig
        self.mutants : list[MutantFileINFO] = []
        self.log = ""

    def add_orig(self, orig: FileINFO):
        self.orig = orig
        
    def add_mutant(self, mutant: MutantFileINFO):
        self.mutants.append(mutant)

    def add_log(self, log: str):
        self.log += log

    def save_log(self):
        with open(f"{self.case_dir}/log.txt", "w") as f:
            f.write(self.log)