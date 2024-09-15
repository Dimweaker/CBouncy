import os
import random
import asyncio

from filemanager import *

CSMITH_HOME = os.environ["CSMITH_HOME"]

class ProgramGenerator:
    def __init__(self, file_path: str, my_args: list[str] = None):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

        if my_args is not None:
            self.my_args = my_args
        else:
            self.my_args = []

    async def generate_program(self, epoch : int) -> FileINFO:
        test_dir = os.path.join(self.file_path, f"case_{epoch}")
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)

        process = await asyncio.create_subprocess_exec(f"{CSMITH_HOME}/bin/csmith",
                                                       "--output", "orig.c",
                                                       *self.my_args, 
                                                       stdout=asyncio.subprocess.PIPE,
                                                       cwd=test_dir)
        await process.communicate()
        return FileINFO(os.path.join(test_dir, "orig.c"))

    async def generate_programs(self, num: int) -> list[CaseManager]:
        print("---Generating programs---")

        case_list = []
        for i in range(num):
            case_list.append(CaseManager(await self.generate_program(i)))
        return case_list

