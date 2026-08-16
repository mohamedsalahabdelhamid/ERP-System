import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Boolean, Numeric, String, create_engine, inspect

from app.db import base  # noqa: F401  (registers all ORM models on Base.metadata)
from app.db.base_class import Base


def upgrade_db(db_url: str) -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(config, "head")


def test_alembic_upgrade_head_creates_sales_and_purchase_invoice_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", db_url)

    upgrade_db(db_url)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "sales_invoices" in tables
    assert "sales_invoice_lines" in tables
    assert "purchase_invoices" in tables
    assert "purchase_invoice_lines" in tables


def test_upgraded_schema_matches_orm_metadata_column_names(tmp_path, monkeypatch):
    """Guard against migration drift: every ORM column must exist after upgrade head.

    This catches the class of bug where a column is added to a model (or a new
    migration is missing) and a fresh database crashes at runtime.
    """
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", db_url)

    upgrade_db(db_url)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    migrated_tables = set(inspector.get_table_names())

    for table in Base.metadata.sorted_tables:
        assert table.name in migrated_tables, f"table {table.name} missing from schema"
        orm_columns = {col.name for col in table.columns}
        db_columns = {col["name"] for col in inspector.get_columns(table.name)}
        missing = orm_columns - db_columns
        extra = db_columns - orm_columns
        assert not missing, f"{table.name} missing columns in schema: {sorted(missing)}"
        assert not extra, f"{table.name} has unexpected columns in schema: {sorted(extra)}"


def test_company_settings_alert_columns_have_correct_types(tmp_path, monkeypatch):
    """The alert settings must be typed to match the ORM (float, bool, string)."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", db_url)

    upgrade_db(db_url)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = {col["name"]: col["type"] for col in inspector.get_columns("company_settings")}

    assert isinstance(columns["low_stock_threshold"], Numeric), columns["low_stock_threshold"]
    assert isinstance(columns["alert_emails"], String), columns["alert_emails"]
    assert isinstance(columns["block_negative_stock"], Boolean), columns["block_negative_stock"]
