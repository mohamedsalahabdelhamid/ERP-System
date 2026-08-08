"""Declarative base for all ORM models.

Business models (companies, users, ...) will subclass ``Base`` starting in
Phase 1. Keeping the base here lets Alembic autogenerate migrations by simply
importing every model's metadata.

A shared naming convention is set so that constraint/index names are stable and
deterministic across migrations (important for Alembic autogenerate).
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
