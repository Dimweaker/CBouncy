import random
import re
import subprocess

from filemanager import CaseManager, FileINFO, ReducePatchFileINFO
from configs import PREFIX_TEXT, SUFFIX_TEXT, OPT_FORMAT, SIMPLE_OPTS, CSMITH_HOME

class Reducer:
    def __init__(self, case : CaseManager, complex_opts: bool = False, timeout: int = 1):
        self.timeout = timeout
        self.case = case
        self.orig_code = case.orig.get_text()
        self.declaration_scope = self.get_declaration_scope(self.orig_code)
        self.complex_opts = complex_opts

    # def reduce:
    #     while True:
    #         # main loop of reducer thread
            
    def reduce_patch(self):
        # reduce a single patch
        for mutant in self.case.mutants:
            reduced_patch_mutant = ReducePatchFileINFO(mutant)
            for func, opts in mutant.function.items():
                for opt in opts:
                    reduced_patch_mutant.function[func].remove(opt)
                    code = self.add_opt(reduced_patch_mutant.function)
                    self.write_to_file(reduced_patch_mutant.filepath, code)
                    self.process_file(reduced_patch_mutant)
                    if reduced_patch_mutant.res != mutant.res:
                        reduced_patch_mutant.function[func].append(opt)
                    else:
                        print(f"Reduced {opt} from {func} in {reduced_patch_mutant.get_basename()}")

            code = self.add_opt(reduced_patch_mutant.function)
            self.write_to_file(reduced_patch_mutant.filepath, code)
            self.process_file(reduced_patch_mutant)



    # def reduce_case():
    #     # reduce a single case
    #
    #     return functions

    @staticmethod
    def get_declaration_scope(raw_code : str) -> str:
        """Get functions from a C source file"""
        declaration_scope = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", raw_code, re.S)
        return declaration_scope.group() if declaration_scope else ""

    def add_opt(self, opt_dict=None) -> str:
        code = self.orig_code
        if opt_dict is None:
            return code

        for key, value in opt_dict.items():
            if self.complex_opts:
                opt_str = ",".join(value)
                code = code.replace(key, f"{key[:-1]} {OPT_FORMAT.format(opt_str)}")
            else:
                code = code.replace(key, f"{key[:-1]} {OPT_FORMAT.format(value)}")

        return code

    @staticmethod
    def write_to_file(mutant_file_path: str, code: str):
        with open(mutant_file_path, "w") as f:
            f.write(code)

    @staticmethod
    def compile_program(file: FileINFO):
        exe = f"{file.get_basename().rstrip('.c')}_gcc.out"

        # disable opts for orig
        if file.is_mutant():
            opts = "-" + random.choice(SIMPLE_OPTS)
            cmd = ["gcc", file.get_abspath(), f"-I{CSMITH_HOME}/include", "-o", exe, "-w", opts]
        else:
            cmd = ["gcc", file.get_abspath(), f"-I{CSMITH_HOME}/include", "-o", exe, "-w"]

        file.set_cmd(" ".join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=file.get_cwd())
        process.communicate()
        if process.returncode != 0:
            # ! compile failed
            file.res = "Compile failed"
        else:
            file.exe = exe

    def run_program(self, file: FileINFO, timeout: float = None):
        # ! reject to run compile failed program
        if file.res == "Compile failed":
            return

        if timeout is None:
            timeout = self.timeout
        try:
            result = subprocess.run(f"./{file.exe}", stdout=subprocess.PIPE, cwd=file.get_cwd(), timeout=timeout)
            output = result.stdout.decode("utf-8")

        except subprocess.TimeoutExpired:
            output = "Timeout"

        file.res = output

    def process_file(self, file: FileINFO, timeout: float = None):
        self.compile_program(file)
        self.run_program(file, timeout=timeout)
