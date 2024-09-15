import os
import random
import shutil
import asyncio

from configs import SIMPLE_OPTS
from filemanager import *

CSMITH_HOME = os.environ["CSMITH_HOME"]

class Oracle:
    def __init__(self, case: CaseManager, timeout: float = 0.3,
                 save_output: bool = True, stop_on_fail: bool = False):
        self.case = case
        self.timeout = timeout
        self.save_output = save_output
        self.stop_on_fail = stop_on_fail

    async def compile_program(self, file: FileINFO):
        exe = f"{file.get_basename().rstrip('.c')}_gcc"
        opts = "-" + random.choice(SIMPLE_OPTS)
        cmd = ["gcc", file.get_abspath(), f"-I{CSMITH_HOME}/include", "-o", exe, "-w", opts]
        file.set_cmd(" ".join(cmd))
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, cwd=file.get_cwd())
        await process.communicate()
        if self.stop_on_fail:
            assert process.returncode == 0, f"Failed to compile {file}"

        return exe

    async def run_program(self, file: FileINFO, exe: str, timeout : float = None):
        if timeout is None:
            timeout = self.timeout
        process = await asyncio.create_subprocess_exec(f"./{exe}", stdout=asyncio.subprocess.PIPE, cwd=file.get_cwd())
        try:
            output, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
            output = output.decode("utf-8")

        except asyncio.TimeoutError:
            output = "Timeout"
            process.kill()

        file.res = output
        return output

    async def process_file(self, file: FileINFO):
        exe = await self.compile_program(file)
        output = await self.run_program(file, exe)
        return exe, output

    async def recheck(self, exe):
        output = await self.run_program(self.case.case_dir, exe, timeout=30)
        return exe, output

    async def test_case(self):
        tasks = []
        tasks.append(self.process_file(self.case.orig))
        for mutant in self.case.mutants:
            tasks.append(self.process_file(mutant))

        outputs = await asyncio.gather(*tasks)
        outputs_dict = {key: value for key, value in outputs}
        outputs = [value for _, value in outputs]

        # find diff in outputs
        if len(set(outputs)) != 1:
            tasks = []
            for exe in outputs_dict.keys():
                tasks.append(self.recheck(exe))
            outputs = await asyncio.gather(*tasks)

            outputs_dict = {key: value for key, value in outputs}
            outputs = [value for _, value in outputs]

        # diff eliminated in recheck
        if len(set(outputs)) == 1:
            print(f"All programs are equivalent with output: {outputs[0].strip()}")
            shutil.rmtree(self.case.case_dir)
            return True
        else:
            print("Programs are not equivalent")
            for key, value in outputs_dict.items():
                print(f"File: {key} Output: {value.strip()}")
            return False
