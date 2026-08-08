"""Auth API endpoints (Phase 1).

    POST /auth/login            -> email + password, returns a bearer token.
    POST /auth/logout           -> revokes the current session.
    POST /auth/select-company   -> sets the active company/branch for the session.
    GET  /auth/me               -> current user, active scope, accessible companies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import get_current_session, get_current_user
from app.modules.auth.models import AuthSession
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    SelectCompanyRequest,
    SessionScope,
    TokenResponse,
    UserRead,
)
from app.modules.auth.service import AuthError
from app.modules.companies import service as company_service
from app.modules.companies.schemas import CompanyRead
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.authenticate_user(db, payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )
    session, raw_token = auth_service.create_session(db, user)
    return TokenResponse(
        access_token=raw_token,
        expires_at=session.expires_at.isoformat(),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> None:
    auth_service.logout(db, session)


@router.post("/select-company", response_model=SessionScope)
def select_company(
    payload: SelectCompanyRequest,
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> SessionScope:
    try:
        session = auth_service.select_company(
            db, session, payload.company_id, payload.branch_id
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        )
    return SessionScope(
        current_company_id=session.current_company_id,
        current_branch_id=session.current_branch_id,
    )


@router.get("/me", response_model=MeResponse)
def me(
    session: AuthSession = Depends(get_current_session),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    companies = company_service.get_user_companies(db, user.id)
    return MeResponse(
        user=UserRead.model_validate(user),
        scope=SessionScope(
            current_company_id=session.current_company_id,
            current_branch_id=session.current_branch_id,
        ),
        companies=[CompanyRead.model_validate(c) for c in companies],
    )
