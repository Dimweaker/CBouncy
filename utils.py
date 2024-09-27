import subprocess
import shutil
import smtplib
from email.message import EmailMessage

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
