import shutil
from multiprocessing import Process
from filemanager import *
from utils import send_mail, zip_dir
from configs import (MAIL_CONFIG,
                     UNCOMPILED, COMPILER_CRASHED, COMPILE_TIMEOUT,
                     RUNTIME_CRASHED, RUNTIME_TIMEOUT)


class Oracle:
    def __init__(self, timeout: float = 20, input_buffer: CaseBuffer = None):
        self.timeout = timeout
        self.input_buffer = input_buffer

        self.oracle_processes = [Process(target=self.test_case) for _ in range(1)] # 5 processes for testing

    def run(self):
        for process in self.oracle_processes:
            process.start()

    def join(self):
        for process in self.oracle_processes:
            process.join()

    @staticmethod
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