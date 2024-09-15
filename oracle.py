import os
import random
import shutil
import asyncio

from optimize_options import SIMPLE_OPTS
from filemanager import *

CSMITH_HOME = os.environ["CSMITH_HOME"]

class Oracle:
    def __init__(self, case: CaseManager, timeout: float = 0.3,
                 save_output: bool = True, stop_on_fail: bool = False):
        self.case = case
        self.timeout = timeout
        self.save_output = save_output
        self.stop_on_fail = stop_on_fail

    async def compile_program(self, root: str, file: str):
        exe = f"{file.rstrip('.c')}_gcc"
        opts = "-" + random.choice(SIMPLE_OPTS)
        cmd = ["gcc", file, f"-I{CSMITH_HOME}/include", "-o", exe, "-w", opts]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, cwd=root)
        await process.communicate()
        if self.stop_on_fail:
            assert process.returncode == 0, f"Failed to compile {file}"
        else:
            self.case.add_log(f"{' '.join(cmd)} : {process.returncode}\n")

        return exe

    async def run_program(self, root: str, exe: str, timeout : float = None):
        if timeout is None:
            timeout = self.timeout
        process = await asyncio.create_subprocess_exec(f"./{exe}", stdout=asyncio.subprocess.PIPE, cwd=root)
        try:
            output, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
            output = output.decode("utf-8")

        except asyncio.TimeoutError:
            output = "Timeout"
            process.kill()
        return output

    async def process_file(self, root: str, file: str):
        exe = await self.compile_program(root, file)
        output = await self.run_program(root, exe)
        self.case.add_log(f"Output for {file}: {output.strip()}\n")
        return exe, output

    async def recheck(self, exe):
        output = await self.run_program(self.case.case_dir, exe, timeout=30)
        self.case.add_log(f"Recheck {exe}: {output.strip()}\n")
        return exe, output

    async def test_programs(self):
        tasks = []
        root = self.case.case_dir
        ori_file = self.case.orig.file
        tasks.append(self.process_file(root, ori_file))
        for mutant in self.case.mutants:
            tasks.append(self.process_file(root, mutant.file))

        outputs = await asyncio.gather(*tasks)
        outputs_dict = {key: value for key, value in outputs}
        outputs = [value for _, value in outputs]

        if len(set(outputs)) != 1:
            tasks = []
            for exe in outputs_dict.keys():
                tasks.append(self.recheck(exe))
            outputs = await asyncio.gather(*tasks)

            outputs_dict = {key: value for key, value in outputs}
            outputs = [value for _, value in outputs]

        if len(set(outputs)) == 1:
            print(f"All programs are equivalent with output: {outputs[0].strip()}")
            shutil.rmtree(self.case.case_dir)
            return True
        else:
            print("Programs are not equivalent")
            for key, value in outputs_dict.items():
                print(f"File: {key} Output: {value.strip()}")
            return False
