"""Shared FastAPI dependencies re-exported for use across business modules.

Business routers (Phase 3+) should import the company-scope dependency from
here so there is a single, stable import path:

    from app.api.deps import get_current_company_id, get_current_user
"""

from app.db.session import get_db  # noqa: F401
from app.modules.auth.dependencies import (  # noqa: F401
    get_current_company_id,
    get_current_session,
    get_current_user,
)
