import os
import threading
from multiprocessing import Queue

class FileINFO:
    def __init__(self, filepath):
        self.filepath = filepath
        self.compile_cmd = ""   # command to run the file
        self.res = None

    def set_cmd(self, cmd: str):
        self.compile_cmd = cmd

    def get_cwd(self) -> str:
        return os.path.dirname(self.filepath)

    def get_basename(self) -> str:
        return os.path.basename(self.filepath)

    def get_abspath(self) -> str:
        return self.filepath

    def get_text(self) -> str:
        with open(self.filepath, 'r') as f:
            text = f.read()
            f.close()
        return text 

    def __str__(self):
        return \
f"""{self.filepath}
    isMutant: 0
    cmd {self.compile_cmd}
    res {self.res}
"""

class MutantFileINFO(FileINFO):
    def __init__(self, path: str, function : dict[str: list[str]] = None):
        super().__init__(path)
        self.compile_cmd = ""
        if function is not None:
            self.function = function
        else:
            self.function : dict[str: list[str]] = dict()

    def add_func_opts(self, function : str, opts : list[str]):
        self.function[function] = opts
    
    def __str__(self):
        func_opts = "\n    ".join([f"{k}\n\t{' '.join(v)}" for k, v in self.function.items()])
        return \
f"""{self.filepath}
    isMutant: 1
    cmd {self.compile_cmd}
    res {self.res}
%%
    {func_opts}
%%
"""

class CaseManager:
    def __init__(self, orig : FileINFO = None):
        self.case_dir = orig.get_cwd()
        self.orig : FileINFO = orig
        self.mutants : list[MutantFileINFO] = []

    def set_orig(self, orig: FileINFO):
        self.orig = orig
        
    def add_mutant(self, mutant: MutantFileINFO):
        self.mutants.append(mutant)

    def get_casename(self) -> str:
        return os.path.basename(self.case_dir)

    def save_log(self):
        with open(f"{self.case_dir}/log", 'w') as f:
            f.write(str(self.orig))
            for mutant in self.mutants:
                f.write(str(mutant))
            f.close()

class CaseBuffer:
    def __init__(self, size):
        self.queue = Queue(size)
        
    def push(self, case: CaseManager):
        self.queue.put(case)
            
    def get(self) -> CaseManager:
        case = self.queue.get(True)
        return case    
        