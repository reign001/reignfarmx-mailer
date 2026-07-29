import os

from dotenv import load_dotenv
import smtplib

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER")

    MAIL_PORT = int(os.getenv("MAIL_PORT"))

    # MAIL_USE_TLS = os.getenv(
    #     "MAIL_USE_TLS",
    #     "False"
    # ).lower() == "true"

    # MAIL_USE_SSL = os.getenv(
    #     "MAIL_USE_SSL",
    #     "False"
    # ).lower() == "true"

    MAIL_USERNAME = "contactperson@reignfarmx.com"

    MAIL_PASSWORD = "Ecoset14#"

    MAIL_DEFAULT_SENDER = "ReignFarmX <contactperson@reignfarmx.com>"
    

    SMTP_SERVER = "smtp.hostinger.com"
    SMTP_PORT = 465

    USERNAME = "contactperson@reignfarmx.com"
    PASSWORD = "Ecoset14#"

    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(USERNAME, PASSWORD)
    print("Login successful!")
    server.quit()