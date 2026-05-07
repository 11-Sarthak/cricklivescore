import os
from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

load_dotenv()

# =========================
# SAFE FALLBACK VALUES
# =========================

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "test@example.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "test")
MAIL_FROM = os.getenv("MAIL_FROM", "test@example.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "CricketApp")

# =========================
# CONNECTION CONFIG (SAFE)
# =========================

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

# =========================
# EMAIL FUNCTION
# =========================

async def send_reset_password_email(email: str, token: str):

    reset_link = f"http://localhost:3000/reset-password?token={token}"

    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=f"Reset link: {reset_link}",
        subtype="plain",
    )

    fm = FastMail(conf)
    await fm.send_message(message)