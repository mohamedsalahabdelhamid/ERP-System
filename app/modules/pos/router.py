from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_current_user,
    get_db,
    require_module,
    require_permission,
)
from app.modules.pos.models import PosOrder, PosSession
from app.modules.pos.schemas import (
    PosOrderCreate,
    PosOrderRead,
    PosSessionClose,
    PosSessionCreate,
    PosSessionRead,
)
from app.modules.pos import service
from app.modules.users.models import User

router = APIRouter(
    prefix="/pos",
    tags=["pos"],
    dependencies=[Depends(require_module("pos"))],
)


@router.get(
    "/sessions",
    response_model=list[PosSessionRead],
    dependencies=[Depends(require_permission("pos.view"))],
)
def list_sessions(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[PosSession]:
    return service.list_sessions(db, company_id)


@router.post(
    "/sessions",
    response_model=PosSessionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("pos.manage"))],
)
def open_session(
    data: PosSessionCreate,
    user: User = Depends(get_current_user),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PosSession:
    return service.open_session(db, company_id, user.id, data)


@router.post(
    "/sessions/{session_id}/close",
    response_model=PosSessionRead,
    dependencies=[Depends(require_permission("pos.manage"))],
)
def close_session(
    session_id: int,
    data: PosSessionClose,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PosSession:
    session = service.get_session(db, company_id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="POS session not found.")
    try:
        return service.close_session(db, session, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/orders",
    response_model=list[PosOrderRead],
    dependencies=[Depends(require_permission("pos.view"))],
)
def list_orders(
    session_id: Optional[int] = Query(default=None),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[PosOrder]:
    return service.list_orders(db, company_id, session_id)


@router.post(
    "/orders",
    response_model=PosOrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("pos.manage"))],
)
def create_order(
    data: PosOrderCreate,
    user: User = Depends(get_current_user),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PosOrder:
    try:
        return service.create_order(db, company_id, user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
