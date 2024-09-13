import os
import shutil
import asyncio

CSMITH_HOME = os.environ["CSMITH_HOME"]

class ProgramTester:
    def __init__(self, file_path: str, timeout: float = 0.3, save_output: bool = False, stop_on_fail: bool = False):
        self.file_path = file_path
        self.timeout = timeout
        self.save_output = save_output
        self.stop_on_fail = stop_on_fail

    @staticmethod
    async def compile_program(root: str, file: str):
        exe = f"{file.strip('.c')}_gcc"
        process = await asyncio.create_subprocess_exec("gcc-9", file,
                                                        f"-I{CSMITH_HOME}/include", "-o", exe, "-w",
                                                        stdout=asyncio.subprocess.PIPE, cwd=root)
        await process.communicate()
        if self.stop_on_fail:
            assert process.returncode == 0, f"Failed to compile {file}"
        else:
            with open(f"{root}/compile_log.txt", "a") as f:
                f.write(f"{file} : {process.returncode}\n")

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
        if self.save_output:
            with open(f"{root}/{exe}.txt", "w") as f:
                f.write(output)
        return exe, output

    async def recheck(self, exe):
        output = await self.run_program(self.file_path, exe, timeout=30)
        return exe, output

    async def test_programs(self):
        tasks = []
        for root, _, files in os.walk(self.file_path):
            for file in files:
                if file.endswith(".c"):
                    tasks.append(self.process_file(root, file))

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
            shutil.rmtree(self.file_path)
            return True
        else:
            print("Programs are not equivalent")
            with open(f"{self.file_path}/outputs.txt", "w") as f:
                for key, value in outputs_dict.items():
                    f.write(f"File: {key} Output: {value}\n")
                    print(f"File: {key} Output: {value}")
            return False
