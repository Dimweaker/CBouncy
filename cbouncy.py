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

args = argparse.ArgumentParser()
args.add_argument("--tmp_path", type=str, default="")
args.add_argument("-t", "--timeout", type=float, default=0.3)
args.add_argument("-s", "--save_output", action='store_true')
args.add_argument("-c", "--complex_opts", action='store_true')
args.add_argument("-m", "--max_opts", type=int, default=35)
args.add_argument("-n_g", "--generate_num", type=int, default=5)
args.add_argument("-n_m", "--mutate_num", type=int, default=10)
args.add_argument("-s_f", "--stop_on_fail", action='store_true')


class CBouncy:
    def __init__(self, test_dir : str, generate_num: int = 5, mutate_num: int = 10,
                 timeout: float = 0.3, max_opts: int = 35, save_output: bool = True,
                 complex_opts: bool = False, stop_on_fail: bool = False, my_args=None):
        self.root_path = os.path.abspath(test_dir)
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)
        self.generate_num = generate_num
        self.mutate_num = mutate_num
        self.max_opts = max_opts
        self.timeout = timeout
        self.save_output = save_output
        self.complex_opts = complex_opts
        self.stop_on_fail = stop_on_fail
        self.my_args = my_args

        buffer1 = CaseBuffer(20)
        buffer2 = CaseBuffer(5)
        self.generator = ProgramGenerator(self.root_path, self.my_args, output_buffer=buffer1)
        self.mutator = CodeMutator(self.complex_opts, self.max_opts, input_buffer=buffer1, output_buffer=buffer2)
        self.oracle = Oracle(self.timeout, self.save_output, self.stop_on_fail, input_buffer=buffer2)

    def run(self):
        print("--- Start testing ---")

        self.generator.run()
        self.mutator.run()
        self.oracle.run()

        self.generator.join()
        self.mutator.join()
        self.oracle.join()

def run(tmp_path: str, generate_num: int = 5, mutate_num: int = 10,
              timeout: float = 0.3, max_opts: int = 35, save_output: bool = True,
              complex_opts: bool = False, stop_on_fail: bool = False, my_args=None):
    if tmp_path == "":
        test_dir = mkdtemp(prefix="tmp_", dir=os.getcwd())

    cb = CBouncy(test_dir, generate_num, mutate_num, timeout,
                 max_opts, save_output, complex_opts, stop_on_fail,
                 my_args)
    cb.run()
    if not os.listdir(test_dir):
        os.rmdir(test_dir)

if __name__ == "__main__":
    args, unknown = args.parse_known_args()
    run(args.tmp_path, args.generate_num, args.mutate_num, args.timeout,
        args.max_opts, args.save_output, args.complex_opts, args.stop_on_fail,
        unknown)
