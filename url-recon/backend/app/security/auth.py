"""
auth.py — password hashing and bearer token helpers.

The goal of this module is to keep authentication mechanics out of the route
handlers. Routes should read like business logic, not like a crypto notebook.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

# PBKDF2 is available in Python's standard library and is appropriate for
# storing password hashes when parameterised with a per-password random salt.
HASH_NAME = "sha256"
PBKDF2_ITERATIONS = 200_000
DEFAULT_AUTH_SECRET = "development-only-change-me"
TOKEN_TTL_SECONDS = 12 * 60 * 60

# HTTPBearer extracts the Authorization: Bearer <token> header for us.
# auto_error=False lets us return our own consistent 401 response.
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """
    Derive a salted PBKDF2 hash and store the algorithm metadata alongside it.

    Stored format:
      pbkdf2_sha256$<iterations>$<salt>$<derived_key>
    """
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_{HASH_NAME}${PBKDF2_ITERATIONS}${salt}${derived_key}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Recreate the PBKDF2 derivation and compare it in constant time.

    hmac.compare_digest() avoids timing leaks that can happen with a plain
    string equality check.
    """
    try:
        algorithm, iterations, salt, expected_hash = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != f"pbkdf2_{HASH_NAME}":
        return False

    recalculated = hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(recalculated, expected_hash)


def _get_auth_secret() -> str:
    """
    Read the signing secret from the environment with a development fallback.

    Production deployments should set APP_AUTH_SECRET to a long random value.
    """
    return os.getenv("APP_AUTH_SECRET", DEFAULT_AUTH_SECRET)


def create_access_token(username: str) -> str:
    """
    Create a compact signed token without adding another dependency.

    The payload is JSON encoded then base64url encoded. The signature is an
    HMAC-SHA256 over that payload using APP_AUTH_SECRET.
    """
    payload = {
        "sub": username,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(
        _get_auth_secret().encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def verify_access_token(token: str) -> str:
    """
    Verify the HMAC signature and expiration, then return the username.

    Any validation failure maps to the same 401 to avoid leaking details about
    which part of the token was wrong.
    """
    try:
        encoded_payload, provided_signature = token.split(".", 1)
    except ValueError as exc:
        raise _unauthorized() from exc

    expected_signature = hmac.new(
        _get_auth_secret().encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise _unauthorized()

    padding = "=" * (-len(encoded_payload) % 4)
    try:
        payload = json.loads(
            base64.urlsafe_b64decode(f"{encoded_payload}{padding}").decode("utf-8")
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise _unauthorized() from exc

    expires_at = payload.get("exp")
    username = payload.get("sub")
    if not isinstance(expires_at, int) or not isinstance(username, str):
        raise _unauthorized()
    if expires_at < int(time.time()):
        raise _unauthorized()
    return username


def _unauthorized() -> HTTPException:
    """
    Build a consistent 401 response used across auth failures.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_authenticated_username(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    FastAPI dependency for protected routes.

    Routes that include `Depends(require_authenticated_username)` can trust that
    a valid bearer token was presented and can use the returned username if
    they need audit context later.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    return verify_access_token(credentials.credentials)
