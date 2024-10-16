import shutil
from multiprocessing import Process
from filemanager import *
from utils import send_mail, zip_dir
from configs import (MAIL_CONFIG,
                     COMPILER_CRASHED, COMPILE_TIMEOUT,
                     RUNTIME_CRASHED, RUNTIME_TIMEOUT)


class Oracle:
    def __init__(self, timeout: float = 20, input_buffer: CaseBuffer = None):
        self.timeout = timeout
        self.input_buffer = input_buffer

        self.oracle_processes = [Process(target=self.test_case) for _ in range(20)] 
        
    def run(self):
        for process in self.oracle_processes:
            process.start()

    def join(self):
        for process in self.oracle_processes:
            process.join()

    @staticmethod
    def check_file(file : FileINFO) -> bool:
        """
        Returns:
            bool: True means a bug found
        """
        res_dict = file.result_dict
        for e in [COMPILE_TIMEOUT, COMPILER_CRASHED, RUNTIME_CRASHED]:
            if e in res_dict.values():
                # a bug found
                return True
                
        res_dict_without_RUNTIME_TIMEOUT = \
            dict(filter(lambda x: x[1] != RUNTIME_TIMEOUT, res_dict.items()))
        res_num = len(set(res_dict_without_RUNTIME_TIMEOUT.values()))
        if res_num == 0:
            file.is_infinite = True # timeout on all opt level
        if res_num > 1:
            # a bug found
            return True
        return False

    @staticmethod
    def check_case(case: CaseManager)-> bool:
        orig = case.orig
        mutants = case.mutants
        for opt in SIMPLE_OPTS:
            orig_res = orig.result_dict[opt]
            for mutant in mutants:
                mutant_res = mutant.result_dict[opt]
                if orig_res != mutant_res:
                    # a bug found
                    return True
        return False

    def test_case(self):
        while True:
            case = self.input_buffer.get()    
            case.process(timeout=60)
            
            # orig file check
            if self.check_file(case.orig):
                self.save_bug(case)
                continue
            
            # case check
            if self.check_case(case):
                self.save_bug(case)
                continue

            # no bug found
            shutil.rmtree(case.case_dir)

    @staticmethod
    def save_bug(case: CaseManager):
        # remove .out files
        subprocess.run(['rm', '*.out'], cwd=case.case_dir)
        case.save_log()
        zip_dir(case.case_dir, case.case_dir)
        send_mail(MAIL_CONFIG, f"A bug is found in {case.case_dir}!",
                  f"A bug is found in {case.case_dir}!\nPlease check the output files.",
                  attachment=case.case_dir + ".zip")