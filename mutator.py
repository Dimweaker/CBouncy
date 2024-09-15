import random
import re

from optimize_options import SIMPLE_OPTS, COMPLEX_OPTS
from filemanager import *

PREFIX_TEXT = "/\* --- FORWARD DECLARATIONS --- \*/"
SUFFIX_TEXT = "/\* --- FUNCTIONS --- \*/"
OPT_FORMAT = '__attribute__((optimize("{}")));'
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

class CodeMutator:
    def __init__(self, case : CaseManager, complex_opts: bool = False, max_opts: int = 35):
        self.case = case
        orig_file = case.orig.filepath
        if orig_file.endswith(".c"):
            self.file_normname = orig_file.split("/")[-1].split(".")[0]
            with open(orig_file, "r") as f:
                self.raw_code = f.read()
        else:
            self.raw_code = orig_file
            self.file_normname = "".join([random.choice(CHARS) for _ in range(6)])
        self.declaration_scope = self.get_declaration_scope()
        self.functions = self.get_functions()
        self.complex_opts = complex_opts
        self.max_opts = max_opts

    def get_declaration_scope(self) -> str:
        """Get forward declarations from a C source file"""
        declaration_scope = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", self.raw_code, re.S)
        return declaration_scope.group() if declaration_scope else ""

    def get_functions(self) -> list[str]:
        """Get functions from a C source file"""
        functions = re.findall(rf"\n(.+?;)", self.declaration_scope, re.S)
        return functions

    def add_opt(self, opt_dict=None) -> (str, dict[str, list[str]]):
        # TODO: store selected opts
        if opt_dict is None:
            funcs = [re.search(rf"(\S*)\(.*\);", func).group() for func in self.functions]
            if self.complex_opts:
                opts_n = random.randint(1, self.max_opts)
                opt_dict = {func: random.sample(COMPLEX_OPTS, opts_n) for func in funcs}
            else:
                opt_dict = {func: random.choice(SIMPLE_OPTS) for func in funcs}

        code = self.raw_code
        for key, value in opt_dict.items():
            if self.complex_opts:
                opt_str = ",".join(value)
                code = code.replace(key, f"{key[:-1]} {OPT_FORMAT.format(opt_str)}")
            else:
                code = code.replace(key, f"{key[:-1]} {OPT_FORMAT.format(value)}")

        return code, opt_dict

    @staticmethod
    def write_to_file(mutant_file_path: str, code: str):
        with open(mutant_file_path, "w") as f:
            f.write(code)

    def mutate(self, num: int = 5):
        for i in range(num):
            code, opt_dict = self.add_opt()
            suffix = "".join([random.choice(CHARS) for _ in range(6)])
            mutant_file = f"{self.case.case_dir}/{self.file_normname}_{suffix}.c"
            self.write_to_file(mutant_file, code)
            self.case.add_mutant(MutantFileINFO(mutant_file, opt_dict))

