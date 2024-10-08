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
                 global_opts: str = "", args: list[str] = None):
        """
        Args:
            filepath: The path of the program.
            compiler: The compiler used to compile this program,
                such as `gcc` or `llvm`.
            global_opts: The global options (which are also arguments).
            args: A list of arguments taken by the compiler.
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
        return f"{self.compiler} {self.abspath} -I{CSMITH_HOME}/include -w {self.global_opts} {' '.join(self.args)} -o {self.exe}".strip()

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
        """Compile the program, and store the result in `self.res` if compilation failed.
        """
        cmd = list(filter(lambda x: x, self.cmd.split(" ")))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=self.cwd)
        process.communicate()
        if process.returncode != 0:
            self.res = "Compile failed"

    def run_program(self, timeout: float = 1):
        """Run the program if it is compilable, and store the result in `self.res`.
        """
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

    def add_opt(self, complex_opts: bool = False, max_opts: int = 35, opt_dict=None, code: str = ""):
        if code:
            raw_code = code
        else:
            raw_code = self.text
        if opt_dict is None:
            declaration_scope = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", raw_code, re.S)
            declaration_scope = declaration_scope.group() if declaration_scope else ""
            functions = re.findall(rf"\n(.+?;)", declaration_scope, re.S)
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
            opt_str = OPT_FORMAT.format(",".join(value) if complex_opts else value[0]) if value else ""
            if key + "(" not in code and value:
                return "", opt_dict
            code = re.sub(rf"({key}\(.*?\)).*?;",
                          lambda r: f"{r.group(1)} {opt_str};",
                          code, count=1)

        return code, opt_dict

    def mutate(self, mutant_file: str = "", complex_opts: bool = False, max_opts: int = 35, opt_dict=None, code: str = ""):
        code, opt_dict = self.add_opt(complex_opts, max_opts, opt_dict, code)

        if code:
            mutant = MutantFileINFO(mutant_file, self.compiler, self.global_opts, self.args, opt_dict)
            mutant.write_to_file(code)
            return mutant
        else:
            return None


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

    def mutate(self, mutant_file: str = "", complex_opts: bool = False, max_opts: int = 35, opt_dict=None, code: str = ""):
        code, _ = self.add_opt(opt_dict=self.functions, code=code)
        self.write_to_file(code)
        return self

    @property
    def fileinfo(self) -> dict:
        fileinfo_dict = super().fileinfo
        fileinfo_dict["functions"] = self.functions
        return fileinfo_dict

    def reduce_patch(self, timeout: float = 1):
        funcs = self.functions.copy()
        res = self.res
        for func, opts in funcs.items():
            self.functions[func].clear()
            self.mutate(opt_dict=self.functions)
            self.process_file(timeout=timeout)
            if self.res == res:
                print(f"Reduced All options from {func} in {self.basename}")
            else:
                self.functions[func] = opts
                for opt in opts:
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
        self.is_infinite_case : bool = False

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
        # TODO: mutate based on self.is_infinite_case
        # ? Suggestion: pass a opts tuple to orig.mutate for sampling
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
                                       file_class: Type[FileINFO] | Type[MutantFileINFO]) \
                                                -> FileINFO | MutantFileINFO:

    fileinfo = file_class(f"{case_dir}/{fileinfo_dict['basename']}", fileinfo_dict["compiler"],
                            fileinfo_dict["global_opts"], fileinfo_dict["args"])
    fileinfo.res = fileinfo_dict["res"]
    return fileinfo

