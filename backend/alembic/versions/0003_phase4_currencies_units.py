"""phase 4: currencies & units

Creates the Phase 4 tables:
  currencies,
  currency_rates,
  unit_conversions

Revision ID: 0003_phase4_currencies_units
Revises: 0002_phase3_master_data
Create Date: 2026-08-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_phase4_currencies_units"
down_revision: Union[str, None] = "0002_phase3_master_data"
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
    # ---- currencies ----
    op.create_table(
        "currencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_currencies_company_id_companies", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_currencies"),
        sa.UniqueConstraint(
            "company_id", "code", name="uq_currencies_company_code"
        ),
    )
    op.create_index("ix_currencies_company_id", "currencies", ["company_id"])

    # ---- currency_rates ----
    op.create_table(
        "currency_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("currency_code", sa.String(length=10), nullable=False),
        sa.Column("rate_to_base", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_currency_rates_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "currency_code"],
            ["currencies.company_id", "currencies.code"],
            name="fk_currency_rates_company_currency", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_currency_rates"),
    )
    op.create_index(
        "ix_currency_rates_company_id", "currency_rates", ["company_id"]
    )

    # ---- unit_conversions ----
    op.create_table(
        "unit_conversions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("from_unit_id", sa.Integer(), nullable=False),
        sa.Column("to_unit_id", sa.Integer(), nullable=False),
        sa.Column("factor", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_unit_conversions_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["from_unit_id"], ["units.id"],
            name="fk_unit_conversions_from_unit_id_units", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["to_unit_id"], ["units.id"],
            name="fk_unit_conversions_to_unit_id_units", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_unit_conversions"),
        sa.UniqueConstraint(
            "company_id", "from_unit_id", "to_unit_id",
            name="uq_unit_conversions_company_from_to",
        ),
    )
    op.create_index(
        "ix_unit_conversions_company_id", "unit_conversions", ["company_id"]
    )

    # ---- sales invoices ----
    op.create_table(
        "sales_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency_code", sa.String(length=10), nullable=False),
        sa.Column("fx_rate", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("total_amount_base", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_sales_invoices_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["partner_id"], ["partners.id"],
            name="fk_sales_invoices_partner_id_partners", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sales_invoices"),
        sa.UniqueConstraint(
            "company_id", "number", name="uq_sales_invoices_company_number"
        ),
    )
    op.create_index("ix_sales_invoices_company_id", "sales_invoices", ["company_id"])
    op.create_index("ix_sales_invoices_partner_id", "sales_invoices", ["partner_id"])

    op.create_table(
        "sales_invoice_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("cost_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("total_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["invoice_id"], ["sales_invoices.id"],
            name="fk_sales_invoice_lines_invoice_id_sales_invoices", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["items.id"],
            name="fk_sales_invoice_lines_item_id_items", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sales_invoice_lines"),
    )
    op.create_index("ix_sales_invoice_lines_invoice_id", "sales_invoice_lines", ["invoice_id"])
    op.create_index("ix_sales_invoice_lines_item_id", "sales_invoice_lines", ["item_id"])

    # ---- purchase invoices ----
    op.create_table(
        "purchase_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency_code", sa.String(length=10), nullable=False),
        sa.Column("fx_rate", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("total_amount_base", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name="fk_purchase_invoices_company_id_companies", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["partner_id"], ["partners.id"],
            name="fk_purchase_invoices_partner_id_partners", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_purchase_invoices"),
        sa.UniqueConstraint(
            "company_id", "number", name="uq_purchase_invoices_company_number"
        ),
    )
    op.create_index("ix_purchase_invoices_company_id", "purchase_invoices", ["company_id"])
    op.create_index("ix_purchase_invoices_partner_id", "purchase_invoices", ["partner_id"])

    op.create_table(
        "purchase_invoice_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("cost_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("total_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["invoice_id"], ["purchase_invoices.id"],
            name="fk_purchase_invoice_lines_invoice_id_purchase_invoices", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["items.id"],
            name="fk_purchase_invoice_lines_item_id_items", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_purchase_invoice_lines"),
    )
    op.create_index("ix_purchase_invoice_lines_invoice_id", "purchase_invoice_lines", ["invoice_id"])
    op.create_index("ix_purchase_invoice_lines_item_id", "purchase_invoice_lines", ["item_id"])


def downgrade() -> None:
    op.drop_table("purchase_invoice_lines")
    op.drop_table("purchase_invoices")
    op.drop_table("sales_invoice_lines")
    op.drop_table("sales_invoices")
    op.drop_table("unit_conversions")
    op.drop_table("currency_rates")
    op.drop_table("currencies")
