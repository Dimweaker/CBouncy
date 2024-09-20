import os
import json
import copy
import subprocess
from multiprocessing import Queue
from shutil import copyfile
from typing import Type

from configs import CSMITH_HOME

class FileINFO:
    def __init__(self, filepath: str, compiler: str = "gcc",
                 global_opts: str = "", args: list[str] = None):
        """

        :param filepath: 要求为一个绝对路径
        :param compiler:
        :param global_opts:
        :param args: 其他参数
        """
        self.compiler = compiler
        self.global_opts = global_opts
        if args is not None:
            self.args = args
        else:
            self.args : list[str] = []
        self.filepath = filepath
        self.res = None

    def is_mutant(self):
        return False

    @property
    def cmd(self) -> str:
        return f"{self.compiler} {self.abspath} -I{CSMITH_HOME}/include -o {self.exe} -w {self.global_opts} {' '.join(self.args)}"

    @property
    def exe(self) -> str:
        return f"{self.basename.rstrip('.c')}_gcc.out"

    @property
    def basename(self) -> str:
        return os.path.basename(self.filepath)

    @property
    def cwd(self) -> str:
        return os.path.dirname(self.filepath)

    @property
    def abspath(self) -> str:
        return self.filepath

    @abspath.setter
    def abspath(self, path: str):
        self.filepath = path

    @property
    def text(self) -> str:
        with open(self.filepath, 'r') as f:
            text = f.read()
            f.close()
        return text

    def copy2dir(self, new_dir : str):
        copyfile(self.filepath, f"{new_dir}/{self.basename}")
        copied_file = copy.deepcopy(self)
        copied_file.abspath = f"{new_dir}/{self.basename}"
        return copied_file


    @property
    def fileinfo(self) -> dict:
        return {
            "basename": self.basename,
            "isMutant": self.is_mutant(),
            "compiler": self.compiler,
            "global_opts": self.global_opts,
            "args": self.args,
            "res": self.res
        }

    def write_to_file(self, code: str):
        with open(self.filepath, "w") as f:
            f.write(code)

    def compile_program(self):
        process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, cwd=self.cwd)
        process.communicate()
        if process.returncode != 0:
            self.res = "Compile failed"

    def run_program(self, timeout: float = 1):
        if self.res == "Compile failed":
            return

        try:
            result = subprocess.run(f"./{self.exe}", stdout=subprocess.PIPE,
                                    cwd=self.cwd, timeout=timeout)
            output = result.stdout.decode("utf-8")

        except subprocess.TimeoutExpired:
            output = "Timeout"

        self.res = output

    def process_file(self, timeout: float = 1):
        self.compile_program()
        self.run_program(timeout=timeout)


class MutantFileINFO(FileINFO):
    def __init__(self, filepath: str, compiler: str = "gcc",
                 global_opts: str = "", args: list[str] = None,
                 functions : dict[str: list[str]] = None):
        super().__init__(filepath, compiler, global_opts, args)
        if functions is not None:
            self.functions = functions.copy()
        else:
            self.functions : dict[str: list[str]] = dict()

    def is_mutant(self):
        return True

    def add_func_opts(self, function : str, opts : list[str]):
        self.functions[function] = opts

    @property
    def fileinfo(self) -> dict:
        fileinfo_dict = super().fileinfo
        fileinfo_dict["functions"] = self.functions
        return fileinfo_dict


class ReducedPatchFileINFO(MutantFileINFO):
    def __init__(self, filepath: str = "", compiler: str = "gcc",
                 global_opts: str = "", args: list[str] = None,
                 functions : dict[str: list[str]] = None,
                 mutant: MutantFileINFO = None):
        if mutant is None:
            super().__init__(filepath, compiler, global_opts, args, functions)
        else:
            reduced_patch_file = mutant.abspath.replace(".c", f"_p.c")
            super().__init__(reduced_patch_file, mutant.compiler,
                             mutant.global_opts, mutant.args,
                             mutant.functions.copy())


class CaseManager:
    def __init__(self, orig : FileINFO = None):
        self.case_dir: str = orig.cwd
        self.orig : FileINFO = orig
        self.mutants : list[MutantFileINFO] = []
        self.reduced_patch_mutants : list[ReducedPatchFileINFO] = []

    def reset_orig(self, orig: FileINFO):
        self.orig = orig
        
    def add_mutant(self, mutant: MutantFileINFO):
        self.mutants.append(mutant)

    def add_reduced_patch_mutant(self, mutant: ReducedPatchFileINFO):
        self.reduced_patch_mutants.append(mutant)

    def is_diff(self) -> bool:
        results = set()
        results.add(self.orig.res)
        for mutant in self.mutants:
            results.add(mutant.res)
        return len(results) != 1

    def process(self, timeout: float = 1):
        self.orig.process_file(timeout=timeout)
        for mutant in self.mutants:
            mutant.process_file(timeout=timeout)

    def recheck(self):
        self.orig.run_program(timeout=60)
        for mutant in self.mutants:
            mutant.run_program(timeout=60)

    def save_log(self):
        json.dump(self.log, open(f"{self.case_dir}/log.json", "w"))

    def copyfiles(self, new_dir : str):
        copied_orig = self.orig.copy2dir(new_dir)
        new_case = CaseManager(copied_orig)
        for mutant in self.mutants:
            new_case.add_mutant(mutant.copy2dir(new_dir))
        for mutant in self.reduced_patch_mutants:
            new_case.add_reduced_patch_mutant(mutant.copy2dir(new_dir))

        return new_case

    @property
    def log(self) -> dict:
        return {
            "case_dir": self.case_dir,
            "orig": self.orig.fileinfo,
            "mutants": [mutant.fileinfo for mutant in self.mutants],
            "reduced_patch_mutants": [mutant.fileinfo for mutant in self.reduced_patch_mutants]
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

    orig = create_fileinfo_from_dict(log["case_dir"], log["orig"], FileINFO)

    case = CaseManager(orig)

    for mutant_info in log["mutants"]:
        mutant = create_fileinfo_from_dict(log["case_dir"], mutant_info, MutantFileINFO)
        case.add_mutant(mutant)

    for mutant_info in log["reduced_patch_mutants"]:
        mutant = create_fileinfo_from_dict(log["case_dir"], mutant_info, ReducedPatchFileINFO)
        case.add_reduced_patch_mutant(mutant)

    return case

def create_fileinfo_from_dict(case_dir: str, fileinfo_dict: dict,
                                       file_class: Type[FileINFO, MutantFileINFO, ReducedPatchFileINFO]) \
                                                -> Type[FileINFO, MutantFileINFO, ReducedPatchFileINFO]:
    if file_class == FileINFO:
        fileinfo = file_class(case_dir + fileinfo_dict["basename"], fileinfo_dict["compiler"],
                              fileinfo_dict["global_opts"], fileinfo_dict["args"])
        fileinfo.res = fileinfo_dict["res"]
    else:
        fileinfo = file_class(case_dir + fileinfo_dict["basename"], fileinfo_dict["compiler"],
                              fileinfo_dict["global_opts"], fileinfo_dict["args"], fileinfo_dict["functions"])
        fileinfo.res = fileinfo_dict["res"]
    return fileinfo

