"""Item master-data API endpoints (Phase 3) — company-scoped CRUD.

Three routers:
  - /item-categories  (categories.view / categories.manage)
  - /units            (units.view / units.manage)
  - /items            (items.view / items.manage)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_company_id, get_db, require_permission
from app.modules.items import service
from app.modules.items.models import Item, ItemCategory, Unit
from app.modules.items.schemas import (
    ItemCategoryCreate,
    ItemCategoryRead,
    ItemCategoryUpdate,
    ItemCreate,
    ItemRead,
    ItemUpdate,
    UnitCreate,
    UnitRead,
    UnitUpdate,
)

categories_router = APIRouter(prefix="/item-categories", tags=["item-categories"])
units_router = APIRouter(prefix="/units", tags=["units"])
items_router = APIRouter(prefix="/items", tags=["items"])


# ============================================================ item categories
def _get_category_or_404(
    db: Session, company_id: int, category_id: int
) -> ItemCategory:
    category = service.get_category(db, company_id, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
        )
    return category


@categories_router.get(
    "",
    response_model=list[ItemCategoryRead],
    dependencies=[Depends(require_permission("categories.view"))],
)
def list_categories(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[ItemCategory]:
    return service.list_categories(db, company_id)


@categories_router.post(
    "",
    response_model=ItemCategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("categories.manage"))],
)
def create_category(
    data: ItemCategoryCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> ItemCategory:
    if service.category_code_exists(db, company_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category code '{data.code}' already exists in this company.",
        )
    if data.parent_id is not None and (
        service.get_category(db, company_id, data.parent_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"parent_id {data.parent_id} not found in this company.",
        )
    return service.create_category(db, company_id, data)


@categories_router.get(
    "/{category_id}",
    response_model=ItemCategoryRead,
    dependencies=[Depends(require_permission("categories.view"))],
)
def get_category(
    category_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> ItemCategory:
    return _get_category_or_404(db, company_id, category_id)


@categories_router.patch(
    "/{category_id}",
    response_model=ItemCategoryRead,
    dependencies=[Depends(require_permission("categories.manage"))],
)
def update_category(
    category_id: int,
    data: ItemCategoryUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> ItemCategory:
    category = _get_category_or_404(db, company_id, category_id)
    if data.code is not None and service.category_code_exists(
        db, company_id, data.code, exclude_id=category.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category code '{data.code}' already exists in this company.",
        )
    return service.update_category(db, category, data)


@categories_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("categories.manage"))],
)
def delete_category(
    category_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    category = _get_category_or_404(db, company_id, category_id)
    service.delete_category(db, category)


# ======================================================================= units
def _get_unit_or_404(db: Session, company_id: int, unit_id: int) -> Unit:
    unit = service.get_unit(db, company_id, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found."
        )
    return unit


@units_router.get(
    "",
    response_model=list[UnitRead],
    dependencies=[Depends(require_permission("units.view"))],
)
def list_units(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[Unit]:
    return service.list_units(db, company_id)


@units_router.post(
    "",
    response_model=UnitRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("units.manage"))],
)
def create_unit(
    data: UnitCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Unit:
    if service.unit_code_exists(db, company_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unit code '{data.code}' already exists in this company.",
        )
    return service.create_unit(db, company_id, data)


@units_router.get(
    "/{unit_id}",
    response_model=UnitRead,
    dependencies=[Depends(require_permission("units.view"))],
)
def get_unit(
    unit_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Unit:
    return _get_unit_or_404(db, company_id, unit_id)


@units_router.patch(
    "/{unit_id}",
    response_model=UnitRead,
    dependencies=[Depends(require_permission("units.manage"))],
)
def update_unit(
    unit_id: int,
    data: UnitUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Unit:
    unit = _get_unit_or_404(db, company_id, unit_id)
    if data.code is not None and service.unit_code_exists(
        db, company_id, data.code, exclude_id=unit.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unit code '{data.code}' already exists in this company.",
        )
    return service.update_unit(db, unit, data)


@units_router.delete(
    "/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("units.manage"))],
)
def delete_unit(
    unit_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    unit = _get_unit_or_404(db, company_id, unit_id)
    service.delete_unit(db, unit)


# ======================================================================= items
def _get_item_or_404(db: Session, company_id: int, item_id: int) -> Item:
    item = service.get_item(db, company_id, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found."
        )
    return item


@items_router.get(
    "",
    response_model=list[ItemRead],
    dependencies=[Depends(require_permission("items.view"))],
)
def list_items(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[Item]:
    return service.list_items(db, company_id)


@items_router.post(
    "",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("items.manage"))],
)
def create_item(
    data: ItemCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Item:
    if service.item_code_exists(db, company_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item code '{data.code}' already exists in this company.",
        )
    error = service.invalid_references(db, company_id, data.model_dump())
    if error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error
        )
    return service.create_item(db, company_id, data)


@items_router.get(
    "/{item_id}",
    response_model=ItemRead,
    dependencies=[Depends(require_permission("items.view"))],
)
def get_item(
    item_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Item:
    return _get_item_or_404(db, company_id, item_id)


@items_router.patch(
    "/{item_id}",
    response_model=ItemRead,
    dependencies=[Depends(require_permission("items.manage"))],
)
def update_item(
    item_id: int,
    data: ItemUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Item:
    item = _get_item_or_404(db, company_id, item_id)
    if data.code is not None and service.item_code_exists(
        db, company_id, data.code, exclude_id=item.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item code '{data.code}' already exists in this company.",
        )
    error = service.invalid_references(
        db, company_id, data.model_dump(exclude_unset=True)
    )
    if error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error
        )
    return service.update_item(db, item, data)


@items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("items.manage"))],
)
def delete_item(
    item_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    item = _get_item_or_404(db, company_id, item_id)
    service.delete_item(db, item)
