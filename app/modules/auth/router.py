"""Auth API endpoints (Phase 1).

    POST /auth/login            -> email + password, returns a bearer token.
    POST /auth/logout           -> revokes the current session.
    POST /auth/select-company   -> sets the active company/branch for the session.
    GET  /auth/me               -> current user, active scope, accessible companies.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import (
    login_allowed,
    record_login_failure,
    record_login_success,
)
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
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    allowed, retry_after = login_allowed(request, payload.email)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        user = auth_service.authenticate_user(db, payload.email, payload.password)
    except AuthError as exc:
        record_login_failure(request, payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )
    record_login_success(request, payload.email)
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
    permissions: list[str] = []
    if session.current_company_id is not None:
        from app.modules.rbac.service import get_user_permissions
        permissions = sorted(get_user_permissions(db, user.id, session.current_company_id))
    # Build a map of company_id -> branch_id from user_roles
    from sqlalchemy import select as sa_select
    from app.modules.rbac.models import UserRole
    user_roles = db.scalars(
        sa_select(UserRole).where(UserRole.user_id == user.id)
    ).all()
    branch_map = {ur.company_id: ur.branch_id for ur in user_roles if ur.branch_id is not None}
    companies_data = []
    for c in companies:
        cr = CompanyRead.model_validate(c)
        cr.branch_id = branch_map.get(c.id)
        companies_data.append(cr)
    return MeResponse(
        user=UserRead.model_validate(user),
        scope=SessionScope(
            current_company_id=session.current_company_id,
            current_branch_id=session.current_branch_id,
        ),
        companies=companies_data,
        is_superuser=user.is_superuser,
        full_name=user.full_name,
        email=user.email,
        permissions=permissions,
    )
