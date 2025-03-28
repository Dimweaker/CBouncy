import os
import json
import copy
import random
import re
import subprocess
from multiprocessing import Queue
from shutil import copyfile
from copy import deepcopy
from typing import Type

from configs import (CSMITH_HOME, UNCOMPILED, 
                     COMPILE_TIMEOUT, COMPILER_CRASHED,
                     RUNTIME_TIMEOUT, RUNTIME_CRASHED,
                     COMPLEX_OPTS_GCC, SIMPLE_OPTS, AGGRESIVE_OPTS,
                     OPT_FORMAT, PREFIX_TEXT, SUFFIX_TEXT)


class FileINFO:
    """A FileINFO includes all info of a single program file.

    Attributes:
        filepath: The path of this program.
        basename: The base name of this program (without path).
        cwd: The directory of this program.
        abspath: The *absolute* path of this program, which is 
            the directory concatenated by the base name.
        text: The content of this program.
        compiler: The compiler used to compile this program,
            such as `gcc` or `llvm`.
        args: A list of arguments taken by the compiler.
        global_opts: The global options (which are also arguments).
        cmd: The command to compile this program.
        exe: The name of the corresponding executable (e.g. `xxx.out`).
        res: The result of executing this program, such as
            `Compile failed`, `Timeout`, etc.
        fileinfo: A dictionary contains multiple attributes of this program.
    """
    def __init__(self, filepath: str, compiler: str = "gcc",
                 args: list[str] = None):
        """
        Args:
            filepath: The path of the program.
            compiler: The compiler used to compile this program,
                such as `gcc` or `llvm`.
            args: A list of arguments taken by the compiler.
        
        ## results of a file has five types:
            1. compile timeout
            2. compiler crashed
            3. runtime timeout
            4. runtime crashed
            5. checksum=xxx     ( program successfully compiled and halted )
        """
        self.compiler : str = compiler
        if args is not None:
            self.args = args
        else:
            self.args: list[str] = []
        self.filepath = filepath
        self.result_dict = dict()
        self.is_infinite = False


    def is_mutant(self):
        return False

    def set_result_dict(self, res_dict: dict[str : str]):
        self.result_dict.clear()
        self.result_dict.update(res_dict)

    @property
    def cmd(self) -> str:
        return f"{self.compiler} {self.abspath} -I{CSMITH_HOME}/include -w {' '.join(self.args)} -o {self.exe}".strip()

    @property
    def exe(self) -> str:
        return f"{self.basename.rstrip('.c')}_{self.compiler}.out"

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

    def copy2dir(self, new_dir: str):
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
            "args": self.args,
            "res_dict": self.result_dict
        }

    def write_to_file(self, code: str):
        with open(self.filepath, "w") as f:
            f.write(code)


    def process_file(self, timeout: float = 1, comp_args: list[str] = None) -> str:
        # compile
        args_str = ' '.join(comp_args)
        if comp_args:
            cmd = list(filter(lambda x: x, self.cmd.split(" ")))+comp_args
        else:
            cmd = list(filter(lambda x: x, self.cmd.split(" ")))
        res = UNCOMPILED
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=self.cwd)

        try:
            process.communicate(timeout=180)
            if process.returncode != 0:
                res = COMPILER_CRASHED
        except subprocess.TimeoutExpired:
            res = COMPILE_TIMEOUT
        print(1)
        # run
        if res == COMPILE_TIMEOUT or res == COMPILER_CRASHED:
            self.result_dict.update({args_str : res})
            return res

        try:
            process = subprocess.run(f"./{self.exe}", 
                                    stdout=subprocess.PIPE,
                                    cwd=self.cwd, timeout=timeout)
            if process.returncode != 0:
                res = RUNTIME_CRASHED
            else:
                res = process.stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            res = RUNTIME_TIMEOUT
        self.result_dict.update({args_str : res})
        return res

    def add_opt(self, max_opts : int, opt_cands: list[str]) -> dict[str : list[str]]:
        code = self.text
        # 1. grep function decls and add opt flags for each
        declaration_scope = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", code, re.S)
        declaration_scope = declaration_scope.group() if declaration_scope else ""
        functions = re.findall(rf"\n(.+?;)", declaration_scope, re.S)
        funcs = [re.search(rf"(\S*)\(.*\).*?;", func).group(1) for func in functions]
        opt_dict = {
            func:
                random.sample(opt_cands, random.randint(1, max_opts))
            for func in funcs
        }
        # 2. generate mutated code 
        code = self.sub_opt(opt_dict, code)
        return code, opt_dict

    def mutate(self, mutant_file: str, max_opts: int, candidate_opts: list[str]):
        code, opt_dict = self.add_opt(max_opts, candidate_opts)

        if code:
            mutant = MutantFileINFO(mutant_file, self.compiler, self.args, opt_dict)
            mutant.write_to_file(code)
            return mutant
        else:
            return None

    @staticmethod
    def sub_opt(opt_dict: dict[str : list[str]], code: str) -> str:
        for key, value in opt_dict.items():
            opt_str = OPT_FORMAT.format(",".join(value))
            code = re.sub(rf"({key}\(.*?\)).*?;",
                          lambda r: f"{r.group(1)} {opt_str};",
                          code, count=1)
        return code


class MutantFileINFO(FileINFO):
    """A MutantFileINFO includes all info of a single mutant program file.

    Attributes:
        filepath: The path of this program.
        basename: The base name of this program (without path).
        cwd: The directory of this program.
        abspath: The *absolute* path of this program, which is 
            the directory concatenated by the base name.
        text: The content of this program.
        compiler: The compiler used to compile this program,
            such as `gcc` or `llvm`.
        args: A list of arguments taken by the compiler.
        global_opts: The global options (which are also arguments).
        cmd: The command to compile this program.
        exe: The name of the corresponding executable (e.g. `xxx.out`).
        res: The result of executing this program, such as
            `Compile failed`, `Timeout`, etc.
        fileinfo: A dictionary contains multiple attributes of this program.
    """
    def __init__(self, filepath: str, compiler: str = "gcc",
                 args: list[str] = None,
                 function_dict : dict[str: list[str]] = None):
        super().__init__(filepath, compiler, args)
        if function_dict is not None:
            self.function_dict = function_dict.copy()
        else:
            self.function_dict : dict[str: list[str]] = dict()

    def is_mutant(self):
        return True

    def add_func_opts(self, function: str, opts: list[str]):
        self.function_dict[function] = opts

    # def mutate(self, mutant_file: str = "", complex_opts: bool = False, max_opts: int = 35, opt_dict=None, code: str = ""):
    #     code, _ = self.add_opt(opt_dict=self.functions, code=code)
    #     self.write_to_file(code)
    #     return self

    @property
    def fileinfo(self) -> dict:
        fileinfo_dict = super().fileinfo
        fileinfo_dict["function_dict"] = self.function_dict
        return fileinfo_dict

    def reduce_patch(self, timeout: float = 1):
        funcs = deepcopy(self.function_dict)
        res = self.result_dict.copy()

        for func, opts in funcs.items():
            # 首先尝试删除所有选项
            self.function_dict[func].clear()
            text = self.sub_opt(self.function_dict, self.text)
            self.write_to_file(text)
            for glob_opt in SIMPLE_OPTS:
                self.process_file(timeout=timeout, comp_args=[glob_opt])

            if all(res[glob_opt] == self.result_dict[glob_opt] for glob_opt in res.keys()):
                print(f"Reduced All options from {func} in {self.basename}")
            else:
                self.function_dict[func] = opts.copy()
                for opt in opts:
                    self.function_dict[func].remove(opt)
                    text = self.sub_opt(self.function_dict, self.text)
                    self.write_to_file(text)
                    for glob_opt in SIMPLE_OPTS:
                        self.process_file(timeout=timeout, comp_args=[glob_opt])
                    if not all(res[glob_opt] == self.result_dict[glob_opt] for glob_opt in res.keys()):
                        self.function_dict[func].append(opt)
                    else:
                        print(f"Reduced {opt} from {func} in {self.basename}")
        text = self.sub_opt(self.function_dict, self.text)
        self.write_to_file(text)


class CaseManager:
    """A CaseManager manages one original files and multiple mutant files, where they are under the same directory.

    Attribute:
        case_dir: The directory of this case.
        orig: The original program.
        mutants: The list of multiple mutants program.
    """
    def __init__(self, orig : FileINFO = None):
        self.orig : FileINFO = orig
        self.mutants : list[MutantFileINFO] = []

        if orig:
            self.case_dir: str = orig.cwd

    def reset_orig(self, orig: FileINFO):
        self.orig = orig
        self.case_dir = orig.cwd
        
    def add_mutant(self, mutant: MutantFileINFO):
        self.mutants.append(mutant)
        mutant.case = self

    # def is_diff(self) -> bool:
    #     results = set()
    #     results.add(self.orig.res)
    #     for mutant in self.mutants:
    #         results.add(mutant.res)
    #     return len(results) != 1

    def process(self, timeout: float = 1):
        for opt in SIMPLE_OPTS:
            self.orig.process_file(timeout=timeout, comp_args=[opt])
            for mutant in self.mutants:
                mutant.process_file(timeout=timeout, comp_args=[opt])

    def save_log(self):
        json.dump(self.log, open(f"{self.case_dir}/log.json", "w"))

    def copyfiles(self, new_dir: str):
        copied_orig = self.orig.copy2dir(new_dir)
        new_case = CaseManager(copied_orig)
        for mutant in self.mutants:
            new_case.add_mutant(mutant.copy2dir(new_dir))

        return new_case

    def mutate_GCC(self, nums: int , complex_opts: bool = False, max_opts: int = 35):
        # TODO: mutate based on self.is_infinite_case
        # ? Suggestion: pass a opts tuple to orig.mutate for sampling
        # generate candidate opts and max_opts
        if complex_opts:
            candidates_GCC = COMPLEX_OPTS_GCC
        else:
            max_opts = 1
            candidates_GCC = SIMPLE_OPTS
        # if not self.is_infinite_case:
        #     candidates_GCC += AGGRESIVE_OPTS
        
        for i in range(nums):
            mutant_file = f"{self.case_dir}/mutant_gcc_{i}.c"
            mutant = self.orig.mutate(mutant_file, max_opts, candidates_GCC)
            self.add_mutant(mutant)

    @property
    def log(self) -> dict:
        return {
            "case_dir": self.case_dir,
            "orig": self.orig.fileinfo,
            "mutants": [mutant.fileinfo for mutant in self.mutants]
        }


class CaseBuffer:
    """A `CaseBuffer` manages a buffer of `CaseManager`.
    """
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

    orig = create_fileinfo_from_dict(log["case_dir"], log["orig"])

    case = CaseManager(orig)

    for mutant_info in log["mutants"]:
        mutant = create_fileinfo_from_dict(log["case_dir"], mutant_info)
        case.add_mutant(mutant)

    return case


def create_fileinfo_from_dict(case_dir: str, fileinfo_dict: dict)\
                                                -> FileINFO | MutantFileINFO:
    if fileinfo_dict["isMutant"]:
        file = MutantFileINFO(f"{case_dir}/{fileinfo_dict['basename']}",
                              fileinfo_dict["compiler"], fileinfo_dict["args"],
                              fileinfo_dict["function_dict"])
        file.set_result_dict(fileinfo_dict["res_dict"])
    else:
        file = FileINFO(f"{case_dir}/{fileinfo_dict['basename']}",
                        fileinfo_dict["compiler"], fileinfo_dict["args"])
        file.set_result_dict(fileinfo_dict["res_dict"])

    return file
