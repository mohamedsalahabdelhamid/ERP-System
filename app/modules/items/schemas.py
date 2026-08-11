"""Pydantic schemas for item master data: categories, units, items."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

ItemType = Literal["stock", "service", "manufactured"]


# ---- Item categories ----
class ItemCategoryCreate(BaseModel):
    name: str
    code: str
    parent_id: Optional[int] = None
    is_active: bool = True


class ItemCategoryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class ItemCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    code: str
    parent_id: Optional[int]
    is_active: bool


# ---- Units ----
class UnitCreate(BaseModel):
    name: str
    code: str
    symbol: Optional[str] = None
    unit_type: Optional[str] = None
    is_active: bool = True


class UnitUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    symbol: Optional[str] = None
    unit_type: Optional[str] = None
    is_active: Optional[bool] = None


class UnitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    code: str
    symbol: Optional[str]
    unit_type: Optional[str]
    is_active: bool


# ---- Unit conversions (Phase 4) ----
class UnitConversionCreate(BaseModel):
    from_unit_id: int
    to_unit_id: int
    factor: float
    is_active: bool = True


class UnitConversionUpdate(BaseModel):
    from_unit_id: Optional[int] = None
    to_unit_id: Optional[int] = None
    factor: Optional[float] = None
    is_active: Optional[bool] = None


class UnitConversionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    from_unit_id: int
    to_unit_id: int
    factor: float
    is_active: bool


# ---- Items ----
class ItemCreate(BaseModel):
    name: str
    code: str
    barcode: Optional[str] = None
    item_category_id: Optional[int] = None
    base_unit_id: Optional[int] = None
    sale_unit_id: Optional[int] = None
    purchase_unit_id: Optional[int] = None
    type: ItemType = "stock"
    default_sale_price: float = 0
    default_purchase_price: float = 0
    min_stock_level: float = 0
    expiry_control: bool = False
    attributes: Optional[dict] = None
    is_active: bool = True


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    barcode: Optional[str] = None
    item_category_id: Optional[int] = None
    base_unit_id: Optional[int] = None
    sale_unit_id: Optional[int] = None
    purchase_unit_id: Optional[int] = None
    type: Optional[ItemType] = None
    default_sale_price: Optional[float] = None
    default_purchase_price: Optional[float] = None
    min_stock_level: Optional[float] = None
    expiry_control: Optional[bool] = None
    attributes: Optional[dict] = None
    is_active: Optional[bool] = None


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    code: str
    barcode: Optional[str]
    item_category_id: Optional[int]
    base_unit_id: Optional[int]
    sale_unit_id: Optional[int]
    purchase_unit_id: Optional[int]
    type: str
    default_sale_price: float
    default_purchase_price: float
    min_stock_level: float
    expiry_control: bool
    attributes: Optional[dict]
    is_active: bool
