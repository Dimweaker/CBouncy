import random
import shutil
from multiprocessing import Process
import subprocess

from configs import SIMPLE_OPTS
from filemanager import *

CSMITH_HOME = os.environ["CSMITH_HOME"]

class Oracle:
    def __init__(self, timeout: float = 0.3,
                 save_output: bool = True, stop_on_fail: bool = False,
                 input_buffer: CaseBuffer = None):
        self.timeout = timeout
        self.save_output = save_output
        self.stop_on_fail = stop_on_fail
        self.input_buffer = input_buffer
        self.oracle_processes = [Process(target=self.test_case) for _ in range(5)] # 5 processes for testing

    def run(self):
        for process in self.oracle_processes:
            process.start()

    def join(self):
        for process in self.oracle_processes:
            process.join()

    def compile_program(self, file: FileINFO):
        exe = f"{file.get_basename().rstrip('.c')}_gcc"
        opts = "-" + random.choice(SIMPLE_OPTS)
        cmd = ["gcc", file.get_abspath(), f"-I{CSMITH_HOME}/include", "-o", exe, "-w", opts]
        file.set_cmd(" ".join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=file.get_cwd())
        process.communicate()
        if self.stop_on_fail:
            assert process.returncode == 0, f"Failed to compile {file}"
        return exe

    def run_program(self, file: FileINFO, exe: str, timeout : float = None):
        if timeout is None:
            timeout = self.timeout
        try:
            result = subprocess.run(f"./{exe}", stdout=subprocess.PIPE, cwd=file.get_cwd(), timeout=timeout)
            output = result.stdout.decode("utf-8")

        except subprocess.TimeoutExpired as e:
            output = "Timeout"

        file.res = output
        return output

    def process_file(self, file: FileINFO):
        exe = self.compile_program(file)
        output = self.run_program(file, exe)
        return exe, output

    def process_case(self, case: CaseManager):
        tasks : dict = {}
        exe, output = self.process_file(case.orig)
        tasks.update({exe: output})
        for mutant in case.mutants:
            exe, output = self.process_file(mutant)
            tasks.update({exe: output})
        return tasks

    def recheck(self, case : CaseManager, exe):
        output = self.run_program(case.case_dir, exe, timeout=30)
        return exe, output

    def test_case(self):
        while True:
            case = self.input_buffer.get()
            results : dict = self.process_case(case)
            outputs = list(results.values())
            exes = results.keys()

            # find diff in outputs
            if len(set(outputs)) != 1:
                results = dict()
                for exe in exes:
                    new_exe, output = self.recheck(case, exe)
                    results.update({new_exe: output})
                outputs = list(results.values())

            # diff eliminated in recheck
            if len(set(outputs)) == 1:
                print(f"All programs are equivalent with output: {outputs[0].strip()}")
                shutil.rmtree(case.case_dir)
                flag = True
            else:
                print("Programs are not equivalent")
                for key, value in results.items():
                    print(f"File: {key} Output: {value.strip()}")
                flag =  False

            if not flag:
                case.save_log()                
