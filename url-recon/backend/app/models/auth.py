"""
auth.py — request/response models for authentication endpoints.

Keeping auth-specific schemas in one module makes the route layer easier to
read and gives us a single place to document the login contract.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Body for POST /api/auth/login.

    We keep this explicit instead of using a plain dict so FastAPI validates the
    shape automatically and returns a clear 422 when fields are missing.
    """

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=255)


class LoginResponse(BaseModel):
    """
    Response returned after a successful login.

    The frontend stores the bearer token locally and sends it on subsequent
    requests in the Authorization header.
    """

    access_token: str
    token_type: str = "bearer"
    username: str


class AuthenticatedUserResponse(BaseModel):
    """
    Lightweight public user profile for session bootstrap.

    We intentionally return only safe fields here and never expose the stored
    password hash.
    """

    username: str
