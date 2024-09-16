import os
import random
import asyncio
from multiprocessing import Process, Value
import subprocess

from filemanager import *

CSMITH_HOME = os.environ["CSMITH_HOME"]

class ProgramGenerator:
    def __init__(self, file_path: str, my_args: list[str] = None, output_buffer: CaseBuffer = None):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
            
        self.epoch = Value('i', 0)
        self.output_buffer = output_buffer
        
        if my_args is not None:
            self.my_args = my_args
        else:
            self.my_args = []

        self.gen_processes = [Process(target=self.generate_case) for _ in range(15)] # processes for csmith program generating

    def generate_case(self):
        while True:
            # generate a csmith program
            stdout = subprocess.run([f"{CSMITH_HOME}/bin/csmith", *self.my_args], 
                                    stdout=subprocess.PIPE).stdout

            orig_program = stdout.decode('utf-8')

            # log
            print(f"--- Generated orig case {self.epoch.value}---")
            # write program to file
            self.epoch.value += 1
            test_dir = os.path.join(self.file_path, f"case_{self.epoch.value}")

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

