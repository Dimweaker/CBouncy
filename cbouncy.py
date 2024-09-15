# /usr/bin/python3

import asyncio
import os
import time
import argparse

from filemanager import *
from generator import ProgramGenerator
from mutator import CodeMutator
from oracle import Oracle

args = argparse.ArgumentParser()
args.add_argument("--tmp_path", type=str, default="tmp")
args.add_argument("-n", "--num_tests", type=int, default=50)
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

    async def run(self):
        print("--- Start testing ---")

        case_list : list[CaseManager] = \
            await ProgramGenerator(self.root_path, self.my_args).generate_programs(self.generate_num)

        print("--- Mutating and testing programs ---")

        for case in case_list:
            cp = CodeMutator(case, self.complex_opts, self.max_opts)
            cp.mutate(self.mutate_num)
            flag = await Oracle(case, self.timeout, self.save_output, self.stop_on_fail).test_case()
            if not flag:
                case.save_log()
            if self.stop_on_fail:
                assert flag, f"Find bugs in {case.case_dir}"
        print("All programs are correct")


async def run(tmp_path: str, epoch_i: int, generate_num: int = 5, mutate_num: int = 10,
              timeout: float = 0.3, max_opts: int = 35, save_output: bool = True,
              complex_opts: bool = False, stop_on_fail: bool = False, my_args=None):
    tmp_path = os.path.abspath(tmp_path)
    print(f"--- Test {epoch_i} ---")
    start = time.time()
    test_dir = os.path.join(tmp_path, f"test_{epoch_i}")

    cb = CBouncy(test_dir, generate_num, mutate_num, timeout,
                 max_opts, save_output, complex_opts, stop_on_fail,
                 my_args)
    await cb.run()
    print(f"--- Test {epoch_i} finished in {time.time() - start} seconds ---")
    if not os.listdir(test_dir):
        os.rmdir(test_dir)
    print()


if __name__ == "__main__":
    args, unknown = args.parse_known_args()
    for i in range(args.num_tests):
        asyncio.run(run(args.tmp_path, i, args.generate_num, args.mutate_num, args.timeout,
                        args.max_opts, args.save_output, args.complex_opts, args.stop_on_fail,
                        unknown))
