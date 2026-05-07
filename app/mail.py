# app/mail.py

import os
from dotenv import load_dotenv
from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
)

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

# =========================
# RESET PASSWORD EMAIL
# =========================

async def send_reset_password_email(
    email: str,
    token: str,
):

    reset_link = (
        f"http://localhost:3000/reset-password?token={token}"
    )

    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=f"""
Hi,

You requested a password reset.

Click the link below to reset your password:

{reset_link}

If you did not request this, please ignore this email.
        """,
        subtype="plain",
    )

    fm = FastMail(conf)

    await fm.send_message(message)