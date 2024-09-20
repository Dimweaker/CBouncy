import shutil
from multiprocessing import Process
from filemanager import *
from mail import send_mail, zip_dir
from configs import MAIL_CONFIG


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

    @staticmethod
    def compile_program(file: FileINFO):
        process = subprocess.Popen(file.cmd, stdout=subprocess.PIPE, cwd=file.cwd)
        process.communicate()
        if process.returncode != 0:
            # ! compile failed
            file.res = "Compile failed"

    def test_case(self):
        while True:
            case = self.input_buffer.get()
            print("--- Testing case ---")

            case.process(self.timeout)
            
            # find diff in outputs
            if case.is_diff():
                case.recheck()

            # diff eliminated in recheck
            if not case.is_diff():
                shutil.rmtree(case.case_dir)
                continue
            
            # ! find bugs!
            case.save_log()
            zip_dir(case.case_dir, case.case_dir)
            send_mail(MAIL_CONFIG, f"A bug is found in {case.case_dir}!",
                      f"A bug is found in {case.case_dir}!\nPlease check the output files.",
                      attachment=case.case_dir + ".zip")
