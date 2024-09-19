import os
import json
from multiprocessing import Queue
from shutil import copyfile

class FileINFO:
    def __init__(self, filepath):
        self.compile_cmd = ""
        self.filepath = filepath
        self.exe : str = ""
        self.res = None

    def is_mutant(self):
        return False

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

    def copy2dir(self, new_dir : str):
        copyfile(self.filepath, f"{new_dir}/{os.path.basename(self.filepath)}")

    @property
    def fileinfo(self) -> dict:
        return {
            "basename": self.get_basename(),
            "isMutant": self.is_mutant(),
            "cmd": self.compile_cmd,
            "res": self.res
        }

    def __str__(self):
        return \
f"""{self.get_basename()}
    isMutant: 0
    cmd {self.compile_cmd}
    res {self.res}
"""

class MutantFileINFO(FileINFO):
    def __init__(self, path: str, function : dict[str: list[str]] = None):
        super().__init__(path)
        self.compile_cmd = ""
        if function is not None:
            self.functions = function
        else:
            self.functions : dict[str: list[str]] = dict()

    def is_mutant(self):
        return True

    def add_func_opts(self, function : str, opts : list[str]):
        self.functions[function] = opts

    @property
    def fileinfo(self) -> dict:
        return {
            "basename": self.get_basename(),
            "isMutant": self.is_mutant(),
            "cmd": self.compile_cmd,
            "res": self.res,
            "functions": self.functions
        }


    def __str__(self):
        func_opts = "\n    ".join([f"{k}\n\t{' '.join(v)}" for k, v in self.functions.items()])
        return \
f"""{self.get_basename()}
    isMutant: 1
    cmd {self.compile_cmd}
    res {self.res}
%%
    {func_opts}
%%
"""

class ReducePatchFileINFO(MutantFileINFO):
    def __init__(self, mutant: MutantFileINFO, function : dict[str: list[str]] = None):
        self.mutant = mutant
        reduced_patch_file = mutant.get_abspath().replace(".c", f"_p.c")
        if function is not None:
            super().__init__(reduced_patch_file, function)
        else:
            super().__init__(reduced_patch_file, mutant.functions.copy())


class CaseManager:
    def __init__(self, orig : FileINFO = None):
        self.case_dir = orig.get_cwd()
        self.orig : FileINFO = orig
        self.mutants : list[MutantFileINFO] = []

    def reset_orig(self, orig: FileINFO):
        self.orig = orig
        
    def add_mutant(self, mutant: MutantFileINFO):
        self.mutants.append(mutant)

    def get_casename(self) -> str:
        return os.path.basename(self.case_dir)

    def is_diff(self) -> bool:
        results = set()
        results.add(self.orig.res)
        for mutant in self.mutants:
            results.add(mutant.res)
        return len(results) != 1

    def save_log(self):
        json.dump(self.log, open(f"{self.case_dir}/log.json", "w"))

    def copyfiles(self, new_dir : str):
        self.orig.copy2dir(new_dir)
        for mutant in self.mutants:
            mutant.copy2dir(new_dir)

    @property
    def log(self) -> dict:
        return {
            "case_dir": self.case_dir,
            "orig": self.orig.fileinfo,
            "mutants": [mutant.fileinfo for mutant in self.mutants]
        }


class CaseBuffer:
    def __init__(self, size: int):
        self.queue = Queue(size)
        
    def push(self, case: CaseManager):
        self.queue.put(case)
            
    def get(self) -> CaseManager:
        case = self.queue.get(True)
        return case    


def create_case_from_log(log: dict | str) -> CaseManager:
    if isinstance(log, str):
        log = json.load(open(log, "r"))

    orig = FileINFO(log["case_dir"] + log["orig"]["basename"])
    orig.compile_cmd = log["orig"]["cmd"]
    orig.res = log["orig"]["res"]

    case = CaseManager(orig)

    for mutant_info in log["mutants"]:
        mutant = MutantFileINFO(log["case_dir"] + mutant_info["basename"],
                                mutant_info["functions"])
        mutant.compile_cmd = mutant_info["cmd"]
        mutant.res = mutant_info["res"]
        case.add_mutant(mutant)

    return case