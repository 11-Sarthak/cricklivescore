import uuid
import os

from typing import Optional

from fastapi import Depends, Request

from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    UUIDIDMixin,
)

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from fastapi_users.db import SQLAlchemyUserDatabase

from app.db import User, get_user_db
from app.mail import send_reset_password_email, conf


# =========================
# SECRET
# =========================

SECRET = os.getenv("SECRET_KEY")


# =========================
# USER MANAGER
# =========================

class UserManager(
    UUIDIDMixin,
    BaseUserManager[User, uuid.UUID],
):

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    # =========================
    # AFTER REGISTER
    # =========================

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ):
        print(f"User {user.id} has registered.")

    # =========================
    # FORGOT PASSWORD EMAIL
    # =========================

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ):

        print(f"Reset token for {user.email}: {token}")

        await send_reset_password_email(
            user.email,
            token,
        )

    # =========================
    # VERIFY EMAIL
    # =========================

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ):

        print(f"Verification token for {user.email}: {token}")


# =========================
# USER MANAGER DEPENDENCY
# =========================

async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    yield UserManager(user_db)


# =========================
# JWT AUTH
# =========================

bearer_transport = BearerTransport(
    tokenUrl="auth/jwt/login"
)


def get_jwt_strategy():
    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=3600,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# =========================
# FASTAPI USERS
# =========================

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(
    active=True,
)