"""FastAPI dependencies for authentication and company scoping.

- get_current_session : resolves the Bearer token to a live AuthSession (401).
- get_current_user    : the authenticated user for the request.
- get_current_company_id : enforces that a company has been selected for the
  session and returns it. Business endpoints (Phase 3+) depend on this so that
  every business request is scoped to a company (spec: "all business queries
  must be filtered by company_id").
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.auth.models import AuthSession
from app.modules.users.models import User


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1].strip()


def get_current_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AuthSession:
    token = _extract_bearer(authorization)
    session = auth_service.get_session_by_token(db, token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session


def get_current_user(
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )
    return user


def get_current_superuser(
    user: User = Depends(get_current_user),
) -> User:
    """The authenticated user must be a platform superuser (403 otherwise)."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform owner access required.",
        )
    return user


def get_current_company_id(
    session: AuthSession = Depends(get_current_session),
) -> int:
    """Return the active company id, or 409 if none has been selected.

    This is the enforcement point for company scoping on business requests.
    """
    if session.current_company_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No company selected. Call /auth/select-company first.",
        )
    return session.current_company_id
