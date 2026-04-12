"""
user_store.py — database access functions for authentication users.

Keeping user persistence separate from route handlers mirrors the existing
scan-store pattern and makes auth logic easier to test.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserRecord
from app.security.auth import hash_password


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"


async def get_user_by_username(
    username: str,
    session: AsyncSession,
) -> UserRecord | None:
    """
    Fetch a single user by username.

    The `users.username` column is indexed and unique, so this query stays fast
    even if more accounts are added later.
    """
    statement = select(UserRecord).where(UserRecord.username == username)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def ensure_default_admin(session: AsyncSession) -> None:
    """
    Seed the default `admin` account on startup if it does not already exist.

    The password is hashed before it ever touches the database.
    """
    existing_user = await get_user_by_username(DEFAULT_ADMIN_USERNAME, session)
    if existing_user is not None:
        return

    session.add(
        UserRecord(
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        )
    )
    await session.commit()
