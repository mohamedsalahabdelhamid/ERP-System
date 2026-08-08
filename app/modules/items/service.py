"""Item master-data service: company-scoped CRUD for categories, units, items.

Every query is filtered by ``company_id``. When an item references a category or
units, the service validates that those rows belong to the *same* company, so a
request can never link to another company's master data.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.items.models import Item, ItemCategory, Unit
from app.modules.items.schemas import (
    ItemCategoryCreate,
    ItemCategoryUpdate,
    ItemCreate,
    ItemUpdate,
    UnitCreate,
    UnitUpdate,
)


# ---------------------------------------------------------------- categories
def list_categories(db: Session, company_id: int) -> list[ItemCategory]:
    stmt = (
        select(ItemCategory)
        .where(ItemCategory.company_id == company_id)
        .order_by(ItemCategory.name)
    )
    return list(db.scalars(stmt).all())


def get_category(
    db: Session, company_id: int, category_id: int
) -> Optional[ItemCategory]:
    stmt = select(ItemCategory).where(
        ItemCategory.id == category_id, ItemCategory.company_id == company_id
    )
    return db.scalar(stmt)


def category_code_exists(
    db: Session, company_id: int, code: str, exclude_id: Optional[int] = None
) -> bool:
    stmt = select(ItemCategory.id).where(
        ItemCategory.company_id == company_id, ItemCategory.code == code
    )
    if exclude_id is not None:
        stmt = stmt.where(ItemCategory.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def create_category(
    db: Session, company_id: int, data: ItemCategoryCreate
) -> ItemCategory:
    category = ItemCategory(company_id=company_id, **data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session, category: ItemCategory, data: ItemCategoryUpdate
) -> ItemCategory:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: ItemCategory) -> None:
    db.delete(category)
    db.commit()


# --------------------------------------------------------------------- units
def list_units(db: Session, company_id: int) -> list[Unit]:
    stmt = select(Unit).where(Unit.company_id == company_id).order_by(Unit.name)
    return list(db.scalars(stmt).all())


def get_unit(db: Session, company_id: int, unit_id: int) -> Optional[Unit]:
    stmt = select(Unit).where(Unit.id == unit_id, Unit.company_id == company_id)
    return db.scalar(stmt)


def unit_code_exists(
    db: Session, company_id: int, code: str, exclude_id: Optional[int] = None
) -> bool:
    stmt = select(Unit.id).where(Unit.company_id == company_id, Unit.code == code)
    if exclude_id is not None:
        stmt = stmt.where(Unit.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def create_unit(db: Session, company_id: int, data: UnitCreate) -> Unit:
    unit = Unit(company_id=company_id, **data.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(db: Session, unit: Unit, data: UnitUpdate) -> Unit:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(db: Session, unit: Unit) -> None:
    db.delete(unit)
    db.commit()


# --------------------------------------------------------------------- items
def list_items(db: Session, company_id: int) -> list[Item]:
    stmt = select(Item).where(Item.company_id == company_id).order_by(Item.name)
    return list(db.scalars(stmt).all())


def get_item(db: Session, company_id: int, item_id: int) -> Optional[Item]:
    stmt = select(Item).where(Item.id == item_id, Item.company_id == company_id)
    return db.scalar(stmt)


def item_code_exists(
    db: Session, company_id: int, code: str, exclude_id: Optional[int] = None
) -> bool:
    stmt = select(Item.id).where(Item.company_id == company_id, Item.code == code)
    if exclude_id is not None:
        stmt = stmt.where(Item.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def invalid_references(db: Session, company_id: int, data: dict) -> Optional[str]:
    """Return an error message if a referenced category/unit is not in company.

    ``data`` is the (partial) item payload. Only keys present are checked, so it
    works for both create and update.
    """
    category_id = data.get("item_category_id")
    if category_id is not None and get_category(db, company_id, category_id) is None:
        return f"item_category_id {category_id} not found in this company."
    for field in ("base_unit_id", "sale_unit_id", "purchase_unit_id"):
        unit_id = data.get(field)
        if unit_id is not None and get_unit(db, company_id, unit_id) is None:
            return f"{field} {unit_id} not found in this company."
    return None


def create_item(db: Session, company_id: int, data: ItemCreate) -> Item:
    item = Item(company_id=company_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: Item, data: ItemUpdate) -> Item:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: Item) -> None:
    db.delete(item)
    db.commit()
