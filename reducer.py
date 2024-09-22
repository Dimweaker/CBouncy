import random
import re
import subprocess
from shutil import copyfile
from tempfile import mkdtemp
import os

from filemanager import CaseManager, CaseBuffer
from configs import PREFIX_TEXT, SUFFIX_TEXT

class Reducer:
    def __init__(self, input_buffer: CaseBuffer, timeout: float = 5):
        self.input_buffer = input_buffer
        self.timeout = timeout

    def reduce(self):
        while True:
            # main loop of reducer thread
            case = self.input_buffer.get()
            # 1. reduce patch for each case
            self.reduce_patch(case)
            # ! case reduction take place in sub tmpdir
            reduce_dir = mkdtemp(dir=case.case_dir)

            new_case = case.copyfiles(reduce_dir)
            new_case.save_log()

            self.reduce_case(reduce_dir)

    def reduce_patch(self, case: CaseManager):
        # reduce a single patch
        for mutant in case.mutants:
            mutant.reduce_patch(timeout=self.timeout)


    def reduce_case(self, reduce_dir: str):
        # ! turn off (pass-clex rename-toks), (pass-clang rename-fun) in creduce
        # TODO: deal with decl reduction in the file
        # backup files
        for root, _, files in os.walk(reduce_dir):
            for file in files:
                copyfile(f"{root}/{file}", f"{root}/{file}.orig")

        # generate a reduce bash