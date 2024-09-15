import os
import random
import asyncio
from tempfile import mkstemp, mkdtemp

CSMITH_HOME = os.environ["CSMITH_HOME"]
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

class ProgramGenerator:
    def __init__(self, file_path: str, my_args: list[str] = None):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

        if my_args is not None:
            self.my_args = my_args
        else:
            self.my_args = []

    async def generate_program(self):
        dir = mkdtemp(prefix="csmith_", dir=self.file_path)
        rel_dir = dir.split("/")[-1]+".c"
        process = await asyncio.create_subprocess_exec(f"{CSMITH_HOME}/bin/csmith", "--output",
                                                       rel_dir, *self.my_args, stdout=asyncio.subprocess.PIPE)
        await process.communicate()
        return root

    async def generate_programs(self, num: int):
        file_list = []
        for i in range(num):
            file_list.append(await self.generate_program())
        return file_list

