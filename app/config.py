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

    MAIL_USERNAME = "contactperson@reignfarmx.com"

    MAIL_PASSWORD = "Ecoset14#"

    MAIL_DEFAULT_SENDER = "ReignFarmX <contactperson@reignfarmx.com>"
    

    SMTP_SERVER = "smtp.hostinger.com"
    SMTP_PORT = 465

    USERNAME = "contactperson@reignfarmx.com"
    PASSWORD = "Ecoset14#"

    MAIL_BATCH_SIZE = 20
    MAIL_SEND_DELAY_SECONDS = 10
    
    HOSTINGER_API_TOKEN="R1N0xSauE0aj6GSf875F3lKPzjLA38R0rIF4wWeu6336c0f5"
    HOSTINGER_ORDER_ID="ORe4e47baf663988c4a2a5789e43d9"
    MAIL_SEND_DELAY_SECONDS = 10
    import os

    MAIL_SEND_DELAY_SECONDS = (MAIL_SEND_DELAY_SECONDS, 10)
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(USERNAME, PASSWORD)
    print("Login successful!")
    server.quit()