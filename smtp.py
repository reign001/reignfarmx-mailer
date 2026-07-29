import smtplib

SMTP_SERVER = "smtp.hostinger.com"
SMTP_PORT = 465

USERNAME = "contactperson@reignfarmx.com"
PASSWORD = "Ecoset14#"

server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
server.login(USERNAME, PASSWORD)
print("Login successful!")
server.quit()