from collections.abc import AsyncGenerator
import uuid
from datetime import datetime
import os

from fastapi import Depends

from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)

from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


# =========================
# DATABASE CONFIG (POSTGRES)
# =========================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/cricapp"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


# =========================
# BASE MODEL
# =========================

class Base(DeclarativeBase):
    pass


# =========================
# USER MODEL
# =========================

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    posts = relationship(
        "Post",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# =========================
# POST MODEL (CLEAN + SAFE)
# =========================

class Post(Base):
    __tablename__ = "posts"

    # Primary Key (UUID as STRING for simplicity + stability)
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Foreign Key (keep as STRING to avoid UUID conflicts)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False,
    )

    caption: Mapped[str | None] = mapped_column(Text)

    url: Mapped[str] = mapped_column(String, nullable=False)

    file_type: Mapped[str] = mapped_column(String, nullable=False)

    file_name: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    user = relationship("User", back_populates="posts")


# =========================
# CREATE TABLES
# =========================

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# =========================
# SESSION DEPENDENCY
# =========================

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# =========================
# USER DB DEPENDENCY
# =========================

async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
):
    yield SQLAlchemyUserDatabase(session, User)