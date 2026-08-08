"""Metadata registry for Alembic and ``create_all``.

Every ORM model must be imported here so that ``Base.metadata`` sees it. Alembic
autogenerate and test ``create_all`` both rely on this being complete.
"""

from app.db.base_class import Base  # noqa: F401

# ---- Phase 1: Multi-Company Core & Auth ----
from app.modules.companies.models import (  # noqa: F401
    Branch,
    Company,
    CompanySettings,
)
from app.modules.users.models import User  # noqa: F401
from app.modules.rbac.models import (  # noqa: F401
    Permission,
    Role,
    RolePermission,
    UserRole,
)
from app.modules.auth.models import AuthSession  # noqa: F401
