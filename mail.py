import smtplib
import json
import time
from email.mime.text import MIMEText
from email.header import Header


def send_mail(config: dict, subject: str, content: str):
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header(config["From"])
    message['To'] = Header(config["To"], 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
    server.login(config["sender"], config["password"])
    server.sendmail(config["sender"], config["receiver"], message.as_string())
    server.quit()


