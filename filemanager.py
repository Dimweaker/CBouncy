import os
import json
import copy
import random
import re
import subprocess
from multiprocessing import Queue
from shutil import copyfile
from typing import Type

from configs import CSMITH_HOME, COMPLEX_OPTS_GCC, SIMPLE_OPTS, OPT_FORMAT, PREFIX_TEXT, SUFFIX_TEXT


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
            self.res = result.stdout.decode("utf-8")
        except subprocess.TimeoutExpired:
            self.res = "Timeout"

    def process_file(self, timeout: float = 1):
        self.compile_program()
        self.run_program(timeout=timeout)

    def add_opt(self, complex_opts: bool = False, max_opts: int = 35, opt_dict=None):
        raw_code = self.text
        declaration_scope = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", raw_code, re.S)
        declaration_scope = declaration_scope.group() if declaration_scope else ""
        functions = re.findall(rf"\n(.+?;)", declaration_scope, re.S)

        if opt_dict is None:
            funcs = [re.search(rf"(\S*)\(.*\).*?;", func).group(1) for func in functions]
            if complex_opts:
                opt_dict = {
                    func:
                        random.sample(COMPLEX_OPTS_GCC, random.randint(1, max_opts))
                    for func in funcs
                }
            else:
                opt_dict = {func: [random.choice(SIMPLE_OPTS)] for func in funcs}
        code = raw_code
        for key, value in opt_dict.items():
            opt_str = ",".join(value) if complex_opts else value[0]
            code = re.sub(rf"({key}\(.*?\)).*?;",
                          lambda r: f"{r.group(1)} {OPT_FORMAT.format(opt_str)};", code)

        return code, opt_dict

    def mutate(self, mutant_file: str = "", complex_opts: bool = False, max_opts: int = 35, opt_dict=None):
        code, opt_dict = self.add_opt(complex_opts, max_opts, opt_dict)

        mutant = MutantFileINFO(mutant_file, self.compiler, self.global_opts, self.args, opt_dict)
        mutant.write_to_file(code)
        return mutant


class MutantFileINFO(FileINFO):
    def __init__(self, filepath: str, compiler: str = "gcc",
                 global_opts: str = "", args: list[str] = None,
                 functions : dict[str: list[str]] = None):
        super().__init__(filepath, compiler, global_opts, args)
        if functions is not None:
            self.functions = functions.copy()
        else:
            self.functions : dict[str: list[str]] = dict()
        if not self.global_opts:
            self.global_opts = random.choice(SIMPLE_OPTS)

    def is_mutant(self):
        return True

    def add_func_opts(self, function : str, opts : list[str]):
        self.functions[function] = opts

    def mutate(self, mutant_file: str = "", complex_opts: bool = False, max_opts: int = 35, opt_dict=None):
        code, _ = self.add_opt(opt_dict=self.functions)
        self.write_to_file(code)
        return self

    @property
    def fileinfo(self) -> dict:
        fileinfo_dict = super().fileinfo
        fileinfo_dict["functions"] = self.functions
        return fileinfo_dict

    def reduce_patch(self, timeout: float = 1):
        funcs = self.functions.copy()
        for func, opts in funcs:
            for opt in opts:
                res = self.res
                self.functions[func].remove(opt)
                self.mutate(opt_dict=self.functions)
                self.process_file(timeout=timeout)
                if self.res != res:
                    self.functions[func].append(opt)
                else:
                    print(f"Reduced {opt} from {func} in {self.basename}")
        self.mutate(opt_dict=self.functions)
        self.process_file(timeout=timeout)


class CaseManager:
    def __init__(self, orig : FileINFO = None):
        self.case_dir: str = orig.cwd
        self.orig : FileINFO = orig
        self.mutants : list[MutantFileINFO] = []

    def reset_orig(self, orig: FileINFO):
        self.orig = orig
        
    def add_mutant(self, mutant: MutantFileINFO):
        self.mutants.append(mutant)

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

        return new_case

    def mutate(self, nums: int , complex_opts: bool = False, max_opts: int = 35, opt_dict=None):
        for i in range(nums):
            mutant_file = f"{self.case_dir}/mutant_{i}.c"
            mutant = self.orig.mutate(mutant_file, complex_opts, max_opts, opt_dict)
            self.add_mutant(mutant)

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

    orig = create_fileinfo_from_dict(log["case_dir"], log["orig"], FileINFO)

    case = CaseManager(orig)

    for mutant_info in log["mutants"]:
        mutant = create_fileinfo_from_dict(log["case_dir"], mutant_info, MutantFileINFO)
        case.add_mutant(mutant)

    return case

def create_fileinfo_from_dict(case_dir: str, fileinfo_dict: dict,
                                       file_class: Type[FileINFO, MutantFileINFO]) \
                                                -> Type[FileINFO, MutantFileINFO]:
    if file_class == FileINFO:
        fileinfo = file_class(case_dir + fileinfo_dict["basename"], fileinfo_dict["compiler"],
                              fileinfo_dict["global_opts"], fileinfo_dict["args"])
        fileinfo.res = fileinfo_dict["res"]
    else:
        fileinfo = file_class(case_dir + fileinfo_dict["basename"], fileinfo_dict["compiler"],
                              fileinfo_dict["global_opts"], fileinfo_dict["args"], fileinfo_dict["functions"])
        fileinfo.res = fileinfo_dict["res"]
    return fileinfo

