"""Authentication service: login, logout, and company/branch selection.

Token lifecycle:
  - login       -> verify credentials, create an AuthSession, return raw token.
  - authenticate-> look up a non-revoked, unexpired session by token hash.
  - logout      -> mark the session revoked.
  - select      -> set current_company_id / current_branch_id on the session.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    generate_token,
    hash_token,
    verify_password,
)
from app.modules.auth.models import AuthSession
from app.modules.companies import service as company_service
from app.modules.users.models import User


class AuthError(Exception):
    """Raised for recoverable auth failures (bad credentials, bad scope)."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password.")
    if not user.is_active:
        raise AuthError("User account is inactive.")
    return user


def create_session(db: Session, user: User) -> tuple[AuthSession, str]:
    """Create a session and return (session, raw_token). Raw token is not stored."""
    raw_token = generate_token()
    expires_at = _utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, raw_token


def get_session_by_token(db: Session, raw_token: str) -> AuthSession | None:
    """Return the live session for a raw token, or None if invalid/expired."""
    session = db.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token))
    )
    if session is None or session.revoked:
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < _utcnow():
        return None
    return session


def logout(db: Session, session: AuthSession) -> None:
    session.revoked = True
    db.add(session)
    db.commit()


def select_company(
    db: Session,
    session: AuthSession,
    company_id: int,
    branch_id: int | None,
) -> AuthSession:
    """Set the active company (and optional branch) for the session."""
    if not company_service.user_can_access_company(
        db, session.user_id, company_id
    ):
        raise AuthError("User has no access to this company.")
    if branch_id is not None and not company_service.branch_belongs_to_company(
        db, branch_id, company_id
    ):
        raise AuthError("Branch does not belong to the selected company.")

    session.current_company_id = company_id
    session.current_branch_id = branch_id
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
