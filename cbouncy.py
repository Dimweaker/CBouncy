import asyncio
import os
import time
import argparse

from program_generator import ProgramGenerator
from code_processor import CodeProcessor
from program_tester import ProgramTester

args = argparse.ArgumentParser()
args.add_argument("-r", "--root_path", type=str, default="tmp")
args.add_argument("-n", "--num_tests", type=int, default=50)
args.add_argument("-t", "--timeout", type=float, default=0.3)
args.add_argument("-s", "--save_output", type=bool, default=True)
args.add_argument("-c", "--complex_opts", type=bool, default=False)
args.add_argument("-m", "--max_opts", type=int, default=35)
args.add_argument("-n_g", "--generate_num", type=int, default=5)
args.add_argument("-n_m", "--mutate_num", type=int, default=10)
args.add_argument("-s_f", "--stop_on_fail", type=bool, default=False)


class CBouncy:
    def __init__(self, root_path : str, generate_num: int = 5, mutate_num: int = 10,
                 timeout: float = 0.3, max_opts: int = 35, save_output: bool = True,
                 complex_opts: bool = False, stop_on_fail: bool = False, my_args=None):
        self.root_path = root_path
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
        print("---Generating programs---")

        file_list = await ProgramGenerator(self.root_path, self.my_args).generate_programs(self.generate_num)

        print("---Mutating and testing programs---")

        for file in file_list:
            pram_name = file.split("/")[-1]
            filename = f"{file}/{pram_name}.c"
            cp = CodeProcessor(filename, self.complex_opts, self.max_opts)
            cp.generate(file, self.mutate_num)
            flag = await ProgramTester(file, self.timeout, self.save_output, self.stop_on_fail).test_programs()
            if self.stop_on_fail:
                assert flag, f"Find bugs in {filename}"
        print("All programs are correct")


async def run(root_path: str, epoch_i: int, generate_num: int = 5, mutate_num: int = 10,
            timeout: float = 0.3, max_opts: int = 35, save_output: bool = True,
              complex_opts: bool = False, stop_on_fail: bool = False, my_args=None):
    print(f"--- Test {epoch_i} ---")
    start = time.time()
    test_name = f"{root_path.strip('/')}/test_{epoch_i}"

    if not os.path.exists(test_name):
        os.makedirs(test_name)
    cb = CBouncy(test_name, generate_num, mutate_num, timeout,
                 max_opts, save_output, complex_opts, stop_on_fail,
                 my_args)
    await cb.run()
    print(f"--- Test {epoch_i} finished in {time.time() - start} seconds ---")
    if not os.listdir(test_name):
        os.rmdir(test_name)
    print()


if __name__ == "__main__":
    args, unknown = args.parse_known_args()
    for i in range(args.num_tests):
        asyncio.run(run(args.root_path, i, args.generate_num, args.mutate_num, args.timeout,
                        args.max_opts, args.save_output, args.complex_opts, args.stop_on_fail,
                        unknown))
