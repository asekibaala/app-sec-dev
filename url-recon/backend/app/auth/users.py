"""
users.py — FastAPI Users configuration for local authentication.

This module centralises the framework wiring:
  - SQLAlchemy user model and adapter
  - User manager
  - JWT authentication backend
  - Current-user dependency for protected routes

It also keeps a deliberate seam for a future external OIDC provider by
isolating the local-auth implementation in one place.
"""

from collections.abc import AsyncGenerator
from typing import Optional
import uuid

from fastapi import Depends, Request
from fastapi_users import FastAPIUsers, exceptions
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.schemas import UserCreate, UserRead, UserUpdate
from app.auth.settings import APP_AUTH_SECRET
from app.database.engine import get_db
from app.database.models import Base

DEFAULT_LOCAL_ADMIN_USERNAME = "admin"
DEFAULT_LOCAL_ADMIN_PASSWORD = "admin"


class AuthUser(SQLAlchemyBaseUserTableUUID, Base):
    """
    Dedicated framework-managed auth table.

    We keep it separate from the earlier ad-hoc `users` table so the new
    FastAPI Users schema can be created safely without relying on implicit
    in-place migrations.
    """

    __tablename__ = "auth_users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)


class AppUserDatabase(SQLAlchemyUserDatabase[AuthUser, uuid.UUID]):
    """
    Small extension over the stock SQLAlchemy adapter so we can authenticate by
    username while still letting FastAPI Users manage hashing and JWT issuance.
    """

    async def get_by_username(self, username: str) -> Optional[AuthUser]:
        statement = select(self.user_table).where(self.user_table.username == username)
        return await self._get_user(statement)


async def get_user_db(session: AsyncSession = Depends(get_db)) -> AsyncGenerator[AppUserDatabase, None]:
    """
    Yield the FastAPI Users database adapter bound to the current async session.
    """
    yield AppUserDatabase(session, AuthUser)


class UserManager(UUIDIDMixin, BaseUserManager[AuthUser, uuid.UUID]):
    """
    Framework user manager for local credentials.

    We override password validation and username authentication behavior while
    still relying on FastAPI Users for hash management and token-compatible flows.
    """

    reset_password_token_secret = APP_AUTH_SECRET
    verification_token_secret = APP_AUTH_SECRET

    async def validate_password(self, password: str, user) -> None:
        """
        Enforce a basic minimum password standard for future non-bootstrap users.
        """
        username = getattr(user, "username", None)
        if username == DEFAULT_LOCAL_ADMIN_USERNAME and password == DEFAULT_LOCAL_ADMIN_PASSWORD:
            return

        if len(password) < 8:
            raise exceptions.InvalidPasswordException(
                reason="Password should be at least 8 characters."
            )

    async def authenticate_username_password(
        self,
        username: str,
        password: str,
    ) -> Optional[AuthUser]:
        """
        Authenticate against the stored username field instead of the framework's
        default e-mail lookup.

        If the stored password hash algorithm changes in the future, the helper
        upgrades it automatically on successful login.
        """
        user = await self.user_db.get_by_username(username)
        if user is None:
            self.password_helper.hash(password)
            return None

        verified, updated_hash = self.password_helper.verify_and_update(
            password,
            user.hashed_password,
        )
        if not verified:
            return None

        if updated_hash is not None:
            await self.user_db.update(user, {"hashed_password": updated_hash})

        return user

    async def on_after_login(
        self,
        user: AuthUser,
        request: Request | None = None,
        response=None,
    ) -> None:
        """
        Hook reserved for future audit logging.
        """
        _ = (user, request, response)


async def get_user_manager(user_db: AppUserDatabase = Depends(get_user_db)) -> AsyncGenerator[UserManager, None]:
    """
    Provide the framework user manager through a FastAPI dependency.
    """
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/api/auth/login")


def get_jwt_strategy() -> JWTStrategy[AuthUser, uuid.UUID]:
    """
    Build the JWT strategy used by the bearer transport.
    """
    return JWTStrategy(secret=APP_AUTH_SECRET, lifetime_seconds=12 * 60 * 60)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[AuthUser, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)


def make_local_admin_create(username: str, password: str) -> UserCreate:
    """
    Build the framework's user-create schema for the seeded local admin.

    FastAPI Users is e-mail based internally, so we map the username to a
    synthetic local-only e-mail address while still authenticating via username.
    """
    return UserCreate(
        username=username,
        email=f"{username}@bugbounty-hut.example.com",
        password=password,
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )


async def ensure_default_local_admin(session: AsyncSession) -> None:
    """
    Seed the local framework-managed admin account if it does not already exist.
    """
    user_db = AppUserDatabase(session, AuthUser)
    existing_user = await user_db.get_by_username(DEFAULT_LOCAL_ADMIN_USERNAME)
    if existing_user is not None:
        return

    manager = UserManager(user_db)
    await manager.create(
        make_local_admin_create(
            DEFAULT_LOCAL_ADMIN_USERNAME,
            DEFAULT_LOCAL_ADMIN_PASSWORD,
        ),
        safe=False,
    )
