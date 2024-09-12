import asyncio
import os
import time

from program_generator import ProgramGenerator
from code_processor import CodeProcessor
from program_tester import ProgramTester


class CBouncy:
    def __init__(self, root_path : str, generate_num: int = 5, mutate_num: int = 10,
                 timeout: float = 0.3, save_output: bool = False):
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
        # for file in file_list:
        #     pram_name = file.split("/")[-1]
        #     filename = f"{file}/{pram_name}.c"
        #     cp = CodeProcessor(filename)
        #     cp.generate(file, self.mutate_num)
        #     flag = await ProgramTester(file, self.timeout, self.save_output).test_programs()
        #     assert flag, f"Find bugs in {filename}"
        for file in file_list:
            pram_name = file.split("/")[-1]
            filename = f"{file}/{pram_name}.c"
            cp = CodeProcessor(filename)
            cp.generate(file, self.mutate_num)
            flag = await ProgramTester(file, self.timeout, self.save_output).test_programs()
            assert flag, f"Find bugs in {filename}"
        print("All programs are correct")


async def run(i):
    print(f"--- Test {i} ---")
    start = time.time()
    test_name = f"tmp/test{i}"
    # if not os.path.exists(test_name):
    #     os.makedirs(test_name)
    # cb = CBouncy(test_name)
    # cb.run()
    if not os.path.exists(test_name):
        os.makedirs(test_name)
    cb = CBouncy(test_name)
    await cb.run()
    print(f"--- Test {i} finished in {time.time() - start} seconds ---")
    print()


if __name__ == "__main__":
    for i in range(50):
        asyncio.run(run(i))