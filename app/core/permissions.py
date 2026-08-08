"""Default permission catalog (Phase 2).

A single source of truth for the permission codes the system knows about. These
codes are synced into the ``permissions`` table by ``app.modules.rbac.seed`` and
referenced by ``require_permission(...)`` on endpoints.

Convention: ``<module>.<action>`` (e.g. "companies.view", "users.manage").
Later phases (sales, inventory, ...) will extend this list with their own codes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDef:
    code: str
    description: str


# ---- Phase 1/2 core permissions ----
DEFAULT_PERMISSIONS: list[PermissionDef] = [
    PermissionDef("companies.view", "View companies and branches"),
    PermissionDef("companies.manage", "Create/update companies and branches"),
    PermissionDef("users.view", "View users"),
    PermissionDef("users.manage", "Create/update users"),
    PermissionDef("roles.view", "View roles"),
    PermissionDef("roles.manage", "Create/update roles and their permissions"),
    PermissionDef("permissions.view", "View the permission catalog"),
]

# All known permission codes (used to grant the Admin role everything).
ALL_PERMISSION_CODES: list[str] = [p.code for p in DEFAULT_PERMISSIONS]
