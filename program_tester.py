import os
import subprocess
import asyncio

CSMITH_HOME = os.environ["CSMITH_HOME"]

class ProgramTester:
    def __init__(self, file_path: str, timeout: float = 0.3, save_output: bool = False):
        self.file_path = file_path
        self.timeout = timeout
        self.save_output = save_output

    # def test_programs(self):
    #     outputs = dict()
    #     for root, _, files in os.walk(self.file_path):
    #         for file in files:
    #             if file.endswith(".c"):
    #                 exe = f"{file.strip('.c')}_gcc"
    #                 process = subprocess.Popen(["gcc", file,
    #                                             f"-I{CSMITH_HOME}/include", "-o", exe, "-w"],
    #                                            stdout=subprocess.PIPE, cwd=root)
    #                 process.communicate()
    #                 try:
    #                     process = subprocess.Popen([f"./{exe}"], stdout=subprocess.PIPE, cwd=root)
    #                     output, _ = process.communicate(timeout=self.timeout)
    #                     output = output.decode("utf-8")
    #                 except subprocess.TimeoutExpired:
    #                     output = "Timeout"
    #
    #                 outputs[file] = output
    #                 if self.save_output:
    #                     with open(f"{root}/{exe}.txt", "w") as f:
    #                         f.write(output)
    #
    #     if len(set(outputs.values())) == 1:
    #         print(f"All programs are equivalent with output: {list(outputs.values())[0].strip()}")
    #         return True
    #     else:
    #         print("Programs are not equivalent")
    #         for key, value in outputs.items():
    #             print(f"File: {key} Output: {value}")
    #         return False

    @staticmethod
    async def compile_program(root: str, file: str):
        exe = f"{file.strip('.c')}_gcc"
        process = await asyncio.create_subprocess_exec("gcc", file,
                                                        f"-I{CSMITH_HOME}/include", "-o", exe, "-w",
                                                        stdout=asyncio.subprocess.PIPE, cwd=root)
        await process.communicate()
        assert process.returncode == 0

        return exe

    async def run_program(self, root: str, exe: str):
        process = await asyncio.create_subprocess_exec(f"./{exe}", stdout=asyncio.subprocess.PIPE, cwd=root)
        try:
            output, _ = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
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


    async def test_programs(self):
        tasks = []
        for root, _, files in os.walk(self.file_path):
            for file in files:
                if file.endswith(".c"):
                    tasks.append(self.process_file(root, file))

        outputs = await asyncio.gather(*tasks)
        outputs_dict = {key: value for key, value in outputs}
        outputs = [value for _, value in outputs]
        if len(set(outputs_dict.values())) == 1:
            print(f"All programs are equivalent with output: {outputs[0].strip()}")
            os.rmdir(self.file_path)
            return True
        else:
            print("Programs are not equivalent")
            for key, value in outputs_dict.items():
                print(f"File: {key} Output: {value}")
            return False

if __name__ == "__main__":
    pt = ProgramTester("tmp/csmith_Ze8luX")
    pt.test_programs()