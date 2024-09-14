import random
import re

from optimize_options import SIMPLE_OPTS, COMPLEX_OPTS

PREFIX_TEXT = "/\* --- FORWARD DECLARATIONS --- \*/"
SUFFIX_TEXT = "/\* --- FUNCTIONS --- \*/"
OPT_FORMAT = '__attribute__((optimize("{}")));'
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

class CodeProcessor:
    def __init__(self, code: str, complex_opts: bool = False, max_opts: int = 35):
        if code.endswith(".c"):
            self.func_name = code.split("/")[-1].split(".")[0]
            with open(code, "r") as f:
                self.raw_code = f.read()
        else:
            self.raw_code = code
            self.func_name = "".join([random.choice(CHARS) for _ in range(6)])
        self.declarations = self.get_declarations()
        self.functions = self.get_functions()
        self.complex_opts = complex_opts
        self.max_opts = max_opts

    def get_declarations(self) -> str:
        """Get forward declarations from a C source file"""
        declarations = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", self.raw_code, re.S)
        return declarations.group() if declarations else ""

    def get_functions(self) -> list[str]:
        """Get functions from a C source file"""
        functions = re.findall(rf"\n(.+?;)", self.declarations, re.S)
        return functions

    def add_opt(self, opt_dict=None):
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

        return code

    @staticmethod
    def write_to_file(file_path: str, code: str):
        with open(file_path, "w") as f:
            f.write(code)

    def generate(self, file_path: str, num: int = 5) -> list[str]:
        file_path = file_path.strip("/")
        file_list = []
        for i in range(num):
            code = self.add_opt()
            suffix = "".join([random.choice(CHARS) for _ in range(6)])
            file_path_ = f"{file_path}/{self.func_name}_{suffix}.c"
            self.write_to_file(file_path_, code)
            file_list.append(file_path_)
        return file_list

