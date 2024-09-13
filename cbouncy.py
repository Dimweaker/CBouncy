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
args.add_argument("-s", "--save_output", type=bool, default=False)
args.add_argument("-n_g", "--generate_num", type=int, default=5)
args.add_argument("-n_m", "--mutate_num", type=int, default=10)
args.add_argument("--save_dir", type=str, default="")

class CBouncy:
    def __init__(self, root_path : str, generate_num: int = 5, mutate_num: int = 10,
                 timeout: float = 0.3, save_output: bool = False, save_dir: str = ""):
        self.root_path = root_path
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)
        self.generate_num = generate_num
        self.mutate_num = mutate_num
        self.timeout = timeout
        self.save_output = save_output

    async def run(self):
        print("--- Start testing ---")
        print("---Generating programs---")
        # file_list = ProgramGenerator(self.root_path).generate_programs(self.generate_num)
        file_list = await ProgramGenerator(self.root_path).generate_programs(self.generate_num)

        print("---Mutating and testing programs---")

        for file in file_list:
            pram_name = file.split("/")[-1]
            filename = f"{file}/{pram_name}.c"
            cp = CodeProcessor(filename)
            cp.generate(file, self.mutate_num)
            flag = await ProgramTester(file, self.timeout, self.save_output).test_programs()
            assert flag, f"Find bugs in {filename}"
        print("All programs are correct")


async def run(root_path: str, epoch_i: int, generate_num: int = 5, mutate_num: int = 10,
                timeout: float = 0.3, save_output: bool = False):
    print(f"--- Test {epoch_i} ---")
    start = time.time()
    test_name = f"{root_path.strip('/')}/test_{epoch_i}"
    # if not os.path.exists(test_name):
    #     os.makedirs(test_name)
    # cb = CBouncy(test_name)
    # cb.run()
    if not os.path.exists(test_name):
        os.makedirs(test_name)
    cb = CBouncy(test_name, generate_num, mutate_num, timeout, save_output)
    await cb.run()
    print(f"--- Test {epoch_i} finished in {time.time() - start} seconds ---")
    if not os.listdir(test_name):
        os.rmdir(test_name)
    print()


if __name__ == "__main__":
    args = args.parse_args()
    for i in range(args.num_tests):
        asyncio.run(run(args.root_path, i, args.generate_num, args.mutate_num, args.timeout, args.save_output, args.save_dir))
