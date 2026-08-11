"""phase 3: master data

Creates the Phase 3 tables:
  partners,
  item_categories, units, items,
  warehouses, warehouse_stock, inventory_movements

Revision ID: 0002_phase3_master_data
Revises: 0001_phase1_core_auth
Create Date: 2026-08-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_phase3_master_data"
down_revision: Union[str, None] = "0001_phase1_core_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    # ---- partners ----
    op.create_table(
        "partners",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("tax_number", sa.String(length=50), nullable=True),
        sa.Column("opening_balance", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("credit_limit", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_partners_company_id_companies", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_partners"),
        sa.UniqueConstraint("company_id", "code", name="uq_partners_company_code"),
    )
    op.create_index("ix_partners_company_id", "partners", ["company_id"])

    # ---- item_categories ----
    op.create_table(
        "item_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_item_categories_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["item_categories.id"],
            name="fk_item_categories_parent_id_item_categories", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_item_categories"),
        sa.UniqueConstraint(
            "company_id", "code", name="uq_item_categories_company_code"
        ),
    )
    op.create_index(
        "ix_item_categories_company_id", "item_categories", ["company_id"]
    )

    # ---- units ----
    op.create_table(
        "units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("unit_type", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_units_company_id_companies", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_units"),
        sa.UniqueConstraint("company_id", "code", name="uq_units_company_code"),
    )
    op.create_index("ix_units_company_id", "units", ["company_id"])

    # ---- items ----
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("barcode", sa.String(length=100), nullable=True),
        sa.Column("item_category_id", sa.Integer(), nullable=True),
        sa.Column("base_unit_id", sa.Integer(), nullable=True),
        sa.Column("sale_unit_id", sa.Integer(), nullable=True),
        sa.Column("purchase_unit_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column(
            "default_sale_price", sa.Numeric(precision=18, scale=4), nullable=False
        ),
        sa.Column(
            "default_purchase_price",
            sa.Numeric(precision=18, scale=4),
            nullable=False,
        ),
        sa.Column(
            "min_stock_level", sa.Numeric(precision=18, scale=4), nullable=False
        ),
        sa.Column("expiry_control", sa.Boolean(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_items_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_category_id"], ["item_categories.id"],
            name="fk_items_item_category_id_item_categories", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["base_unit_id"], ["units.id"],
            name="fk_items_base_unit_id_units", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["sale_unit_id"], ["units.id"],
            name="fk_items_sale_unit_id_units", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["purchase_unit_id"], ["units.id"],
            name="fk_items_purchase_unit_id_units", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_items"),
        sa.UniqueConstraint("company_id", "code", name="uq_items_company_code"),
    )
    op.create_index("ix_items_company_id", "items", ["company_id"])

    # ---- warehouses ----
    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_warehouses_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"], ["branches.id"],
            name="fk_warehouses_branch_id_branches", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_warehouses"),
        sa.UniqueConstraint(
            "company_id", "code", name="uq_warehouses_company_code"
        ),
    )
    op.create_index("ix_warehouses_company_id", "warehouses", ["company_id"])

    # ---- warehouse_stock ----
    op.create_table(
        "warehouse_stock",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("average_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_warehouse_stock_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["warehouse_id"], ["warehouses.id"],
            name="fk_warehouse_stock_warehouse_id_warehouses", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["items.id"],
            name="fk_warehouse_stock_item_id_items", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_warehouse_stock"),
        sa.UniqueConstraint(
            "warehouse_id", "item_id", name="uq_warehouse_stock_warehouse_item"
        ),
    )
    op.create_index(
        "ix_warehouse_stock_company_id", "warehouse_stock", ["company_id"]
    )
    op.create_index(
        "ix_warehouse_stock_warehouse_id", "warehouse_stock", ["warehouse_id"]
    )
    op.create_index("ix_warehouse_stock_item_id", "warehouse_stock", ["item_id"])

    # ---- inventory_movements ----
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_from_id", sa.Integer(), nullable=True),
        sa.Column("warehouse_to_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("total_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_inventory_movements_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["items.id"],
            name="fk_inventory_movements_item_id_items", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["warehouse_from_id"], ["warehouses.id"],
            name="fk_inventory_movements_warehouse_from_id_warehouses",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["warehouse_to_id"], ["warehouses.id"],
            name="fk_inventory_movements_warehouse_to_id_warehouses",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_inventory_movements"),
    )
    op.create_index(
        "ix_inventory_movements_company_id", "inventory_movements", ["company_id"]
    )
    op.create_index(
        "ix_inventory_movements_item_id", "inventory_movements", ["item_id"]
    )


def downgrade() -> None:
    op.drop_table("inventory_movements")
    op.drop_table("warehouse_stock")
    op.drop_table("warehouses")
    op.drop_table("items")
    op.drop_table("units")
    op.drop_table("item_categories")
    op.drop_table("partners")
