import random
import re
import subprocess
from shutil import copyfile
from tempfile import mkdtemp
from multiprocessing import Process

from filemanager import CaseManager, CaseBuffer
from configs import SCRIPT

class Reducer:
    def __init__(self, input_buffer: CaseBuffer, timeout: float = 5):
        self.input_buffer = input_buffer
        self.timeout = timeout

        self.reduce_processes = [Process(target=self.reduce) for _ in range(5)]

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

            self.reduce_case(new_case)

    def reduce_patch(self, case: CaseManager):
        # reduce a single patch
        for mutant in case.mutants:
            mutant.reduce_patch(timeout=self.timeout)

    @staticmethod
    def reduce_case(case: CaseManager):
        # ! turn off (pass-clex rename-toks), (pass-clang rename-fun) in creduce
        # TODO: deal with decl reduction in the file
        # backup files
        script = SCRIPT.format(case.case_dir)
        with open("reduce.sh", "w") as f:
            f.write(script)
            f.close()
        subprocess.run(["creduce", "reduce.sh", case.orig.abspath])



        # generate a reduce bash

    def run(self):
        for process in self.reduce_processes:
            process.start()

    def join(self):
        for process in self.reduce_processes:
            process.join()



if __name__ == "__main__":
    from filemanager import create_case_from_log
    # case = create_case_from_log("/home/dimweaker/dev/compiler_test/tmp_v_n3v4yw/case_535/log.json")
    # for mutant in case.mutants:
    #     mutant.reduce_patch(timeout=5)
    # new_dir = mkdtemp(dir=case.case_dir)
    # new_case = case.copyfiles(new_dir)
    # new_case.save_log()
    # Reducer.reduce_case(new_case)
    case = create_case_from_log("/home/dimweaker/dev/compiler_test/tmp_v_n3v4yw/case_535/tmplogipzea/log.json")
    Reducer.reduce_case(case)
