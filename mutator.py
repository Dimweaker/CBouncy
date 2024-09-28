import random
import re
from multiprocessing import Process

from filemanager import *


class CodeMutator:
    def __init__(self, mutate_num=5, complex_opts: bool = False, max_opts: int = 35,
                 gen_gcc: bool = True, gen_clang: bool = False,
                 input_buffer : CaseBuffer = None, output_buffer : CaseBuffer = None):
        self.mutate_num = mutate_num
        self.complex_opts = complex_opts
        self.max_opts = max_opts
        self.gen_gcc = gen_gcc
        self.gen_clang = gen_clang
        self.input_buffer = input_buffer
        self.output_buffer = output_buffer
        self.mutate_processes = [Process(target=self.mutate) for _ in range(5)]

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

    def mutate(self):
        # TODO: gen variants for gcc and clang
        while True:
            case = self.input_buffer.get()
            
            # main mutate
            if self.gen_gcc:
                case.mutate_GCC(self.mutate_num, self.complex_opts, self.max_opts)
            if self.gen_clang:
                pass
            
            self.output_buffer.push(case)