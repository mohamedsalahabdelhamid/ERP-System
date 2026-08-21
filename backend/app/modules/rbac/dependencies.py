"""FastAPI dependency for permission enforcement (Phase 2).

``require_permission("companies.view")`` returns a dependency that:

1. resolves the current user (via ``get_current_user`` -> 401 if unauthenticated),
2. resolves the active company (via ``get_current_company_id`` -> 409 if none
   selected), and
3. checks that the user holds the given permission code **in that company**,
   raising 403 otherwise.

Permissions are always evaluated within the active company (spec: access
control is per-company), so the dependency composes on top of the existing
company-scope enforcement.

Usage::

    @router.get("", dependencies=[Depends(require_permission("companies.view"))])
    def list_companies(...): ...

``require_module("sales")`` is the licensing check: it returns 403 when the
active company has not been granted the module (see app.core.modules).
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_company_id, get_current_user
from app.modules.companies.models import CompanySettings
from app.modules.rbac import service as rbac_service
from app.modules.users.models import User


def require_permission(code: str) -> Callable[..., None]:
    """Build a dependency that enforces ``code`` within the active company."""

    def _dependency(
        user: User = Depends(get_current_user),
        company_id: int = Depends(get_current_company_id),
        db: Session = Depends(get_db),
    ) -> None:
        if not rbac_service.user_has_permission(db, user.id, company_id, code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {code}",
            )

    return _dependency


def require_module(module: str) -> Callable[..., None]:
    """Build a dependency that 403s when the module is not licensed."""

    def _dependency(
        user: User = Depends(get_current_user),
        company_id: int = Depends(get_current_company_id),
        db: Session = Depends(get_db),
    ) -> None:
        settings = db.get(CompanySettings, company_id)
        if settings is None or module not in (settings.enabled_modules or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Module '{module}' is not enabled for this company.",
            )
        # Superusers are exempt from module licensing (platform owner).
        if user.is_superuser:
            return

    return _dependency
