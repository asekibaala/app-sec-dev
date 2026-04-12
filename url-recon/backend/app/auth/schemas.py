"""
schemas.py — FastAPI Users-compatible Pydantic schemas.

The framework expects user schemas with an e-mail field. We keep a separate
username field because the product requirement is to log in with `admin`, not
with an e-mail address.
"""

import uuid

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Public user payload returned by session bootstrap routes."""

    username: str


class UserCreate(schemas.BaseUserCreate):
    """Schema used when seeding or creating local auth users."""

    username: str = Field(min_length=1, max_length=64)


class UserUpdate(schemas.BaseUserUpdate):
    """Schema reserved for future user-management routes."""

    username: str | None = Field(default=None, min_length=1, max_length=64)


class LoginRequest(BaseModel):
    """
    Product-facing login body.

    We keep this wrapper so the frontend can continue to authenticate with a
    username/password JSON payload instead of an OAuth2 form body.
    """

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=255)


class LoginResponse(BaseModel):
    """Minimal login response returned after FastAPI Users issues a token."""

    access_token: str
    token_type: str


class AuthenticatedUserResponse(BaseModel):
    """Small session bootstrap payload for the frontend."""

    username: str
    model_config = ConfigDict(from_attributes=True)
