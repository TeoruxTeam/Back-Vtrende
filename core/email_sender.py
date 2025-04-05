from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from pydantic import EmailStr

from core.logger import logger


class EmailSender:

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        start_tls: bool,
        start_ssl: bool,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.start_tls = start_tls
        self.start_ssl = start_ssl

    async def send_email(self, email: EmailStr, subject: str, message: str):
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        try:
            if self.start_tls:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    start_tls=True,
                    username=self.username,
                    password=self.password,
                )
            elif self.start_ssl:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    username=self.username,
                    password=self.password,
                    use_tls=True,
                )
            else:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    username=self.username,
                    password=self.password,
                )
            print("Email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
