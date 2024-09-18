import json
import random
import shutil
from multiprocessing import Process
import subprocess

from configs import SIMPLE_OPTS
from filemanager import *
from mail import send_mail, zip_dir

CSMITH_HOME = os.environ["CSMITH_HOME"]
with open("config.json", "r") as f:
    MAIL_CONFIG = json.load(f)

class Oracle:
    def __init__(self, timeout: float = 20, input_buffer: CaseBuffer = None):
        self.timeout = timeout
        self.input_buffer = input_buffer

        self.oracle_processes = [Process(target=self.test_case) for _ in range(5)] # 5 processes for testing

    def run(self):
        for process in self.oracle_processes:
            process.start()

    def join(self):
        for process in self.oracle_processes:
            process.join()

    def compile_program(self, file: FileINFO):
        exe = f"{file.get_basename().rstrip('.c')}_gcc.out"

        # disable opts for orig
        if file.is_mutant():
            opts = "-" + random.choice(SIMPLE_OPTS)
            cmd = ["gcc", file.get_abspath(), f"-I{CSMITH_HOME}/include", "-o", exe, "-w", opts]
        else:
            cmd = ["gcc", file.get_abspath(), f"-I{CSMITH_HOME}/include", "-o", exe, "-w"]
            
        file.set_cmd(" ".join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=file.get_cwd())
        process.communicate()
        if process.returncode != 0:
            # ! compile failed
            file.res = "Compile failed"
        else:
            file.exe = exe

    def run_program(self, file: FileINFO, timeout : float = None):
        # ! reject to run compile failed program
        if file.res == "Compile failed":
            return
            
        if timeout is None:
            timeout = self.timeout
        try:
            result = subprocess.run(f"./{file.exe}", stdout=subprocess.PIPE, cwd=file.get_cwd(), timeout=timeout)
            output = result.stdout.decode("utf-8")

        except subprocess.TimeoutExpired as e:
            output = "Timeout"

        file.res = output

    def process_file(self, file: FileINFO, timeout : float = None):
        self.compile_program(file)
        self.run_program(file, timeout=timeout)

    def process_case(self, case: CaseManager):
        self.process_file(case.orig)
        for mutant in case.mutants:
            self.process_file(mutant)

    def recheck_case(self, case : CaseManager):
        self.run_program(case.orig, timeout=60)
        for mutant in case.mutants:
            self.run_program(mutant, timeout=60)

    def test_case(self):
        while True:
            case = self.input_buffer.get()
            print("--- Testing case ---")

            self.process_case(case)
            
            # find diff in outputs
            if case.is_diff():
                self.recheck_case(case)

            # diff eliminated in recheck
            if not case.is_diff():
                shutil.rmtree(case.case_dir)
                continue
            
            # ! find bugs!
            case.save_log()
            send_mail(MAIL_CONFIG, f"A bug is found in {case.case_dir}!",
                      f"A bug is found in {case.case_dir}!\nPlease check the output files.",
                      attachment=case.case_dir + ".zip")
