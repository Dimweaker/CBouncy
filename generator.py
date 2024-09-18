import os
import random
import asyncio
from multiprocessing import Process, Value
import subprocess

from filemanager import *

CSMITH_HOME = os.environ["CSMITH_HOME"]

class ProgramGenerator:
    def __init__(self, test_dir: str, generate_num=100, csmith_args: list[str] = [], output_buffer: CaseBuffer = None):
        self.test_dir = test_dir
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        self.generate_num = generate_num
        self.epoch = Value('i', 0)
        self.output_buffer = output_buffer
        self.csmith_args = csmith_args

        self.gen_processes = [Process(target=self.generate_case) for _ in range(15)] # processes for csmith program generating

    def generate_case(self):
        while True:
            # generate a csmith program
            stdout = subprocess.run([f"{CSMITH_HOME}/bin/csmith", *self.csmith_args], 
                                    stdout=subprocess.PIPE).stdout

            orig_program = stdout.decode('utf-8')

            # write program to file
            with self.epoch.get_lock():
                self.epoch.value += 1
                test_dir = os.path.join(self.test_dir, f"case_{self.epoch.value}")

            if not os.path.exists(test_dir):
                os.makedirs(test_dir)

            with open(os.path.join(test_dir, "orig.c"), 'w') as f:
                f.write(orig_program)
                f.close()

            case = CaseManager(FileINFO(os.path.join(test_dir, "orig.c")))
            self.output_buffer.push(case)

    def run(self):
        for process in self.gen_processes:
            process.start()

    def join(self):
        for process in self.gen_processes:
            process.join()

