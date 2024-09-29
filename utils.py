import subprocess
import shutil
import smtplib
import os
from email.message import EmailMessage

from filemanager import FileINFO, MutantFileINFO, CaseManager
from configs import (SIMPLE_OPTS, CSMITH_HOME, UNCOMPILED,
                     COMPILE_TIMEOUT, COMPILER_CRASHED,
                     RUNTIME_CRASHED, RUNTIME_TIMEOUT)

def send_mail(config: dict, subject: str, content: str, attachment: str = None):
    message = EmailMessage()
    message['From'] = config["From"]
    message['To'] = config["To"]
    message['Subject'] = subject
    server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
    server.login(config["sender"], config["password"])
    message.set_content(content)
    if attachment is not None:
        with open(attachment, 'rb') as f:
            message.add_attachment(f.read(), maintype='application', subtype='zip', filename=attachment)
    server.send_message(message, config["sender"], config["receiver"])
    server.quit()


def zip_dir(dir_path: str, zip_path: str):
    shutil.make_archive(zip_path, 'zip', dir_path)

def compile_file(cmd: list, cwd: str=None)-> str:
    """compile a program to execution file

    Args:
        cmd (list): command to exec
        cwd (str, optional): cwd for subprocess. Defaults to None.

    Returns:
        tuple[str, str]: comp_res
    """
    process = subprocess.Popen(cmd, cwd=cwd, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate()
    if process.returncode != 0:
        err_msg = process.stderr.decode('utf-8')
        if "segmentation fault" in err_msg:
            return "Compile crashed"
        else:
            return "Compile failed"
    return "Compile success"

def get_file_res_dict(file: str):
    res_dict = {}
    for opt in SIMPLE_OPTS:
        res = UNCOMPILED
        cmd = ["gcc", opt, file, f"-I{CSMITH_HOME}/include", "-w"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=os.path.dirname(file))
        try:
            process.communicate(timeout=60)
            if process.returncode != 0:
                res = COMPILER_CRASHED
        except subprocess.TimeoutExpired:
            res = COMPILE_TIMEOUT
        # run
        if res == COMPILE_TIMEOUT or res == COMPILER_CRASHED:
            res_dict.update({opt : res})
            return res
        try:
            process = subprocess.run(f"./a.out", 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    cwd=os.path.dirname(file), timeout=10)
            if process.stderr.decode('utf-8'):
                res = RUNTIME_CRASHED
            else:
                res = process.stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            res = RUNTIME_TIMEOUT
        res_dict.update({opt : res})
    return res_dict

def create_log_from_dir(case_dir : str):
    case = CaseManager()
    for root, _, files in os.walk(case_dir):
        for file in files:
            if not file.endswith('.c'):
                continue
            abs_path = os.path.join(root, file)
            if file=='orig.c':
                orig_info = FileINFO(abs_path)
                case.reset_orig(orig_info)
            else:
                mutant_file = MutantFileINFO(abs_path)
                case.add_mutant(mutant_file)
    case.process(timeout=20)
    case.save_log()