# /usr/bin/python3

import asyncio
import os
import time
import argparse
from tempfile import mkdtemp

from filemanager import *
from generator import ProgramGenerator
from mutator import CodeMutator
from oracle import Oracle
from reducer import Reducer

args = argparse.ArgumentParser()
args.add_argument("-t", "--timeout", type=float, default=0.3)
args.add_argument("-c", "--complex_opts", action='store_true')
args.add_argument("-m", "--max_opts", type=int, default=35)
args.add_argument("--tmp_path", type=str, default="")
args.add_argument("--gen_clang", action="store_true")
args.add_argument("--gen_gcc", action="store_true")
args.add_argument("--generate_num", type=int, default=100)
args.add_argument("--mutate_num", type=int, default=5)

class CBouncy:
    def __init__(self, test_dir : str, generate_num: int = 100, mutate_num: int = 10,
                 timeout: float = 0.3, max_opts: int = 35,
                 gen_gcc: bool = True, gen_clang: bool = False,
                 complex_opts: bool = False, csmith_args=None):
        buffer1 = CaseBuffer(20)
        buffer2 = CaseBuffer(5)
        buffer3 = CaseBuffer(5)
        self.generator = ProgramGenerator(test_dir, generate_num, csmith_args, output_buffer=buffer1)
        self.mutator = CodeMutator(mutate_num, complex_opts, max_opts, gen_gcc, gen_clang, input_buffer=buffer1, output_buffer=buffer2)
        self.oracle = Oracle(timeout, input_buffer=buffer2)
        self.reducer = Reducer(input_buffer=buffer3, timeout=timeout)

    def run(self):
        print("--- Start testing ---")

        self.generator.run()
        self.mutator.run()
        self.oracle.run()
        self.reducer.run()

        self.generator.join()
        self.mutator.join()
        self.oracle.join()
        self.reducer.join()

def run(args = None, csmith_args=None):
    if args.tmp_path:
        test_dir = os.path.abspath(args.tmp_path)
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
    else:
        test_dir = mkdtemp(prefix="tmp_", dir=os.getcwd())

    gen_gcc = args.gen_gcc
    gen_clang = args.gen_clang
    if not gen_gcc and not gen_clang:
        print("No compiler selected. Defaulted to gcc...")
        gen_gcc = True

    generate_num = args.generate_num
    mutate_num = args.mutate_num
    timeout = args.timeout
    max_opts = args.max_opts
    complex_opts = args.complex_opts

    cb = CBouncy(test_dir, generate_num, mutate_num, timeout,
                 max_opts, gen_gcc, gen_clang, complex_opts,
                 csmith_args)
    cb.run()
    if not os.listdir(test_dir):
        os.rmdir(test_dir)

if __name__ == "__main__":
    args, csmith_args = args.parse_known_args()
    run(args, csmith_args)
