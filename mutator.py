import random
import re
from multiprocessing import Process

from configs import SIMPLE_OPTS, COMPLEX_OPTS
from filemanager import *

PREFIX_TEXT = "/\* --- FORWARD DECLARATIONS --- \*/"
SUFFIX_TEXT = "/\* --- FUNCTIONS --- \*/"
OPT_FORMAT = '__attribute__((optimize("{}")));'
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

class CodeMutator:
    def __init__(self, complex_opts: bool = False, max_opts: int = 35,
                 input_buffer : CaseBuffer = None, output_buffer : CaseBuffer = None):
        self.complex_opts = complex_opts
        self.max_opts = max_opts
        self.input_buffer = input_buffer
        self.output_buffer = output_buffer
        self.mutate_processes = [Process(target=self.mutate) for _ in range(5)]

    @staticmethod
    def get_functions(raw_code : str) -> list[str]:
        """Get functions from a C source file"""
        declaration_scope = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", raw_code, re.S)
        declaration_scope = declaration_scope.group() if declaration_scope else ""
        functions = re.findall(rf"\n(.+?;)", declaration_scope, re.S)
        return functions

    def add_opt(self, case : CaseManager, opt_dict=None) -> list[str, dict[str, list[str]]]:
        raw_code = case.orig.get_text()
        functions = self.get_functions(raw_code)

        # TODO: store selected opts
        if opt_dict is None:
            funcs = [re.search(rf"(\S*)\(.*\);", func).group() for func in functions]
            if self.complex_opts:
                opts_n = random.randint(1, self.max_opts)
                opt_dict = {func: random.sample(COMPLEX_OPTS, opts_n) for func in funcs}
            else:
                opt_dict = {func: [random.choice(SIMPLE_OPTS)] for func in funcs}

        code = raw_code
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

    def run(self):
        for process in self.mutate_processes:
            process.start()

    def join(self):
        for process in self.mutate_processes:
            process.join()

    def mutate(self, num: int = 5):
        while True:
            case = self.input_buffer.get()
            print(f"--- Mutating case {case.get_casename()} ---")
            
            # main mutate
            for i in range(num):
                code, opt_dict = self.add_opt(case)
                mutant_file = f"{case.case_dir}/case_{i}.c"
                self.write_to_file(mutant_file, code)
                case.add_mutant(MutantFileINFO(mutant_file, opt_dict))
            
            print(f"--- Finished mutating case {case.case_dir} ---")
            self.output_buffer.push(case)