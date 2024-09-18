import os
from tempfile import mkdtemp
from shutil import copyfile

from filemanager import CaseManager, CaseBuffer

class Reducer:
    def __init__(self, inputbuffer: CaseBuffer):
        self.inputbuffer = inputbuffer

    def reduce(self):
        while True:
            # main loop of reducer thread
            case = self.inputbuffer.get()
            # 1. reduce patch for each case
            self.reduce_patch(case)
            # ! case reduction take place in sub tmpdir
            reduce_dir = mkdtemp(dir=case.case_dir)
            case.copyfiles(reduce_dir)
            # 2. generate a case log
            case.save_log()
            copyfile(f"{case.case_dir}/log", f"{reduce_dir}/log")
            # 3. reduce case depending on orig.c
            self.reduce_case(reduce_dir)
            
    def reduce_patch(self, case):
        # reduce a single patch
        pass
        
    def reduce_case(self, reduce_dir: str):
        # ! turn off (pass-clex rename-toks), (pass-clang rename-fun) in creduce
        # TODO: deal with decl reduction in the file
        # backup files
        for root, _, files in os.walk(reduce_dir):
            for file in files:
                copyfile(f"{root}/{file}", f"{root}/{file}.orig")

        # generate a reduce bash