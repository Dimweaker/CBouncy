import shutil
from multiprocessing import Process
from filemanager import *
from utils import send_mail, zip_dir
from configs import (MAIL_CONFIG,
                     UNCOMPILED, COMPILER_CRASHED, COMPILE_TIMEOUT,
                     RUNTIME_CRASHED, RUNTIME_TIMEOUT)


class Oracle:
    """class to describe oracle    

    ## the oracle consists of two parts:
    - single file check:
        1. compile file and exec.
        2.1 if result is a checksum, then set this as orig's result and step into part two.
        2.2 if result is other than "RUNTIME TIMEOUT" or "checksum=xxx", report a bug, and discard all mutants.
        2.3 if result is "RUNTIME TIMEOUT", recheck it:
            3.1 compile file on all SIMPLE_OPTS and exec.
            3.2 if results are only "RUNTIME TIMEOUT", then consider the program unhaltable.
            3.3 if results contain identical checksum, then consider the program haltable and step into part two.
            3.4 if results diff in checksum or contains other than checksum and "RUNTIME TIMEOUT", report a bug, and discard all mutants.
        
    - diff between orig and mutants:
        1.1 if all mutants generate same checksum as orig's, then no bug and discard it.
        1.2 if results are: 
            2.1 orig.c: checksum, and a mutant: "RUNTIME TIMEOUT", it's undetermined whether a bug is triggered.
            2.2 orig.c: "RUNTIME TIMEOUT", and a mutant: checksum, report a bug
            2.3 orig.c and a mutant: "RUNTIME TIMEOUT", treat as no bug
    """
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

    def check_file(file: FileINFO) -> bool:
        file.process_file(timeout=60)
        if file.res == COMPILE_TIMEOUT or file.res == COMPILER_CRASHED or file.res == RUNTIME_CRASHED:
            # report a bug
            return True
        elif file.res == RUNTIME_TIMEOUT:
            results_dict = {opt : file.process_file(timeout=60, comp_args=[opt]) for opt in SIMPLE_OPTS}
            results = list(results_dict.values)
            if COMPILE_TIMEOUT in results or COMPILER_CRASHED in results or RUNTIME_CRASHED in results:
                # report a bug
                return True
            else:
                results_dict_without_runtime_timeout = dict(filter(lambda x: x[1] != RUNTIME_TIMEOUT, results_dict.items()))
                if len(results_dict_without_runtime_timeout) == 0:
                    # consider the file as unhaltable
                    file.res = RUNTIME_TIMEOUT
                    return False
                elif len(results_dict_without_runtime_timeout) > 1:
                    # checksum diffs, a bug found
                    return True
                else:
                    opt, res = list(results_dict_without_runtime_timeout.items())[0]
                    file.global_opts = opt
                    file.res = res
        return False

    def test_case(self):
        while True:
            case = self.input_buffer.get()
            ### single file check
            # first check orig.c
            if self.check_file(case.orig):
                # a bug found, discards all mutants
                pass
                continue
            
            # check mutants
            for mutant in case.mutants:
                if self.check_file(mutant):
                    # a bug found, discards others
                    pass
                    continue
                
            ### metamorphic check

    @staticmethod
    def save_bug(case: CaseManager):
        # remove .out files
        subprocess.run(['rm', '*.out'], cwd=case.case_dir)
        case.save_log()
        zip_dir(case.case_dir, case.case_dir)
        send_mail(MAIL_CONFIG, f"A bug is found in {case.case_dir}!",
                  f"A bug is found in {case.case_dir}!\nPlease check the output files.",
                  attachment=case.case_dir + ".zip")