"""Metadata registry for Alembic.

Alembic imports ``Base`` from this module to discover all tables via
``Base.metadata``. Every ORM model added in later phases must be imported here
so that autogenerate can see it.

Phase 0: no business models exist yet, so only the Base is exported.
"""

from app.db.base_class import Base  # noqa: F401

# Later phases will import models here, e.g.:
#   from app.modules.companies.models import Company, Branch  # noqa: F401
