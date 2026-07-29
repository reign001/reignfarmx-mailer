import smtplib
import ssl
import os
from flask import current_app
import smtplib
from email.message import EmailMessage

from email.message import EmailMessage


import smtplib
import traceback
from email.message import EmailMessage
from flask import current_app


class EmailService:

    @staticmethod
    def send_email(recipient, subject, body):

        try:

            server = current_app.config["MAIL_SERVER"]
            port = current_app.config["MAIL_PORT"]
            username = current_app.config["MAIL_USERNAME"]
            password = current_app.config["MAIL_PASSWORD"]
            sender = current_app.config["MAIL_DEFAULT_SENDER"]

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            msg.set_content(body)

            smtp = smtplib.SMTP_SSL(server, port)

            smtp.login(username, password)

            smtp.send_message(msg)

            print("Email sent")

            smtp.quit()

            return True, None

        except Exception as e:

            traceback.print_exc()

            return False, str(e)