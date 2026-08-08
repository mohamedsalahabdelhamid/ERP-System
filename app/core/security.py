"""Security helpers: password hashing and opaque access tokens.

- Passwords are hashed with bcrypt.
- Access tokens are random opaque strings. Only their SHA-256 hash is stored in
  the database (``auth_sessions.token_hash``); the raw token is returned to the
  client once at login and never persisted in clear text.
"""

import hashlib
import secrets

import bcrypt


# ---- Passwords ----

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# ---- Access tokens ----

def generate_token() -> str:
    """Generate a new URL-safe random access token (the raw secret)."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest used to store/look up a token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
